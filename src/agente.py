"""
Agente principal de gestão de crises em itinerários de viagem.

Implementa o grafo LangGraph com StateGraph, contendo nós para validação,
consulta de APIs (voo, clima, transporte), RAG, análise LLM e geração
do plano de contingência.
"""

import re

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.estado import EstadoCrise
from src.ferramentas.clima import consultar_clima
from src.ferramentas.transporte import consultar_transporte_alternativo
from src.ferramentas.voo import consultar_status_voo
from src.rag.busca import BuscaSemantica
from src.rag.documentos import DOCUMENTOS_POLITICAS
from src.validacao import validar_codigo_reserva, validar_mensagem, verificar_dominio


def _get_llm():
    """Retorna instância do ChatGroq (lazy-loaded para permitir dotenv)."""
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _extrair_codigo_reserva(texto: str) -> str:
    """Extrai código de reserva (6 caracteres alfanuméricos A-Z0-9) do texto.

    Tenta encontrar um padrão de 6 caracteres alfanuméricos maiúsculos no texto.
    Se não encontrar com maiúsculas, tenta case-insensitive e converte para upper.
    Retorna string vazia se não encontrar um código válido isolado.
    """
    # Busca direta por 6 chars alfanuméricos maiúsculos (boundary - palavra isolada)
    match = re.search(r'\b([A-Z0-9]{6})\b', texto)
    if match:
        return match.group(1)

    # Tenta case-insensitive (palavra isolada com boundary)
    match = re.search(r'\b([A-Za-z0-9]{6})\b', texto)
    if match:
        candidato = match.group(1).upper()
        # Verifica se parece um código (mistura letras e números OU é puramente numérico/alfanumérico)
        # Descarta palavras comuns do português que tenham 6 chars
        palavras_comuns = {
            "QUANDO", "PORQUE", "MINHA", "MINHA", "CHEGOU", "SAIU",
            "PARTIR", "CHEGAR", "CLASSE", "VIAGEM", "AEREO", "BRASIL",
            "AGENDA", "CANCELA", "ATRASO", "STATUS", "RESERV", "PRECIS",
            "CONSIG", "INFORM", "DESTINO", "ORIGEM",
        }
        if candidato not in palavras_comuns and re.match(r'^[A-Z0-9]{6}$', candidato):
            # Só aceita se tem pelo menos 1 dígito E 1 letra (padrão típico de reserva)
            # OU se é todo numérico (alguns códigos são assim)
            tem_letra = any(c.isalpha() for c in candidato)
            tem_digito = any(c.isdigit() for c in candidato)
            if tem_letra and tem_digito:
                return candidato

    # Não encontrou código válido — retorna vazio
    return ""


def _extrair_mensagem(texto: str, codigo: str) -> str:
    """Extrai a mensagem do usuário removendo o código de reserva do texto."""
    # Remove o código encontrado do texto
    mensagem = texto.replace(codigo, "", 1).strip()
    # Remove também a versão lowercase se existir
    mensagem = mensagem.replace(codigo.lower(), "", 1).strip()
    # Remove pontuação inicial residual
    mensagem = mensagem.lstrip(".,;:- ")
    return mensagem if mensagem else texto


def _parse_status_voo(resultado: str) -> dict:
    """Parseia a string retornada por consultar_status_voo em um dict."""
    dados = {}
    for linha in resultado.strip().split("\n"):
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            chave_limpa = chave.strip().lower().replace(" ", "_")
            dados[chave_limpa] = valor.strip()
    return dados


def _parse_clima(resultado: str) -> dict:
    """Parseia a string retornada por consultar_clima em um dict."""
    dados = {"texto_completo": resultado}
    for linha in resultado.strip().split("\n"):
        linha_strip = linha.strip()
        if ":" in linha_strip:
            chave, valor = linha_strip.split(":", 1)
            chave_limpa = chave.strip().lower().replace(" ", "_").replace("⚠️_", "").replace("✅_", "")
            dados[chave_limpa] = valor.strip()
    # Detectar condições adversas
    if "CONDIÇÕES ADVERSAS DETECTADAS" in resultado:
        dados["condicoes_adversas"] = True
    else:
        dados["condicoes_adversas"] = False
    return dados


def _parse_transporte(resultado: str) -> list:
    """Parseia a string retornada por consultar_transporte_alternativo em uma lista."""
    opcoes = []
    for linha in resultado.strip().split("\n"):
        linha_strip = linha.strip()
        if linha_strip and linha_strip[0].isdigit() and "." in linha_strip:
            opcoes.append(linha_strip)
    return opcoes if opcoes else [resultado]


# ---------------------------------------------------------------------------
# Nós do grafo
# ---------------------------------------------------------------------------

def _eh_consulta_clima_direta(texto: str) -> tuple[bool, str]:
    """Detecta se a mensagem é uma consulta de clima direta (sem necessidade de código de reserva).

    Retorna (True, codigo_aeroporto) se encontrar cidade/aeroporto, ou (False, "").
    Retorna (True, "DESTINO_MEMORIA") se menciona "destino" sem cidade específica,
    indicando que o sistema deve usar o destino da sessão.
    """
    texto_lower = texto.lower()

    # Verificar se é uma pergunta sobre clima/tempo/previsão
    padroes_clima = [
        r"previs[aã]o\s+(do|de)\s+tempo",
        r"como\s+(est[aá]|ta)\s+(o\s+)?(clima|tempo)",
        r"clima\s+(em|no|na|de|do)",
        r"tempo\s+(em|no|na|de|do)",
        r"temperatura\s+(em|no|na|de|do)",
        r"condi[çc][oõ]es?\s+(clim[aá]tica|meteorol[oó]gica)",
    ]

    eh_clima = any(re.search(p, texto_lower) for p in padroes_clima)
    if not eh_clima:
        return False, ""

    # Mapeamento de cidades/nomes para códigos de aeroporto
    cidades_aeroportos = {
        "são paulo": "GRU", "sao paulo": "GRU", "guarulhos": "GRU", "gru": "GRU",
        "rio de janeiro": "GIG", "rio": "GIG", "galeão": "GIG", "galeao": "GIG", "gig": "GIG",
        "brasília": "BSB", "brasilia": "BSB", "bsb": "BSB",
        "salvador": "SSA", "ssa": "SSA",
        "belo horizonte": "CNF", "confins": "CNF", "cnf": "CNF",
        "curitiba": "CWB", "cwb": "CWB",
        "porto alegre": "POA", "poa": "POA",
        "recife": "REC", "rec": "REC",
    }

    for cidade, codigo in cidades_aeroportos.items():
        if cidade in texto_lower:
            return True, codigo

    # Se menciona "destino" ou "meu voo" — usar destino da memória
    if re.search(r"(no|do|ao)\s+destino", texto_lower) or "meu voo" in texto_lower:
        return True, "DESTINO_MEMORIA"

    return False, ""


def _eh_pergunta_sobre_voo(texto: str) -> bool:
    """Detecta se a mensagem é uma pergunta sobre voo/reserva/viagem que requer código."""
    texto_lower = texto.lower()
    padroes_voo = [
        r"\b(meu|minha)\s+voo",
        r"status\s+(do|de)\s+(meu|minha)?\s*voo",
        r"hor[aá]rio\s+(do|de)\s+(meu|minha)?\s*voo",
        r"data\s+(do|de)\s+(meu|minha)?\s*voo",
        r"(meu|minha)\s+reserva",
        r"(meu|minha)\s+(conex[aã]o|escala)",
        r"voo\s+(est[aá]|foi|sera|será)",
        r"quando\s+(sai|parte|chega|decola)",
        r"onde\s+(est[aá]|fica)\s+(meu|minha)",
        r"cancelad[oa]\s+(meu|o\s+meu)",
        r"atrasad[oa]\s+(meu|o\s+meu)",
        r"(meu|minha)\s+itiner[aá]rio",
        r"(meu|minha)\s+passagem",
        r"(meu|minha)\s+viagem",
    ]
    return any(re.search(p, texto_lower) for p in padroes_voo)


def validacao_node(state: EstadoCrise) -> dict:
    """Nó de validação: extrai código e mensagem, valida formato e domínio."""
    erros = []

    # Extrair texto da última mensagem do usuário
    mensagens = state.get("messages", [])
    texto_usuario = ""
    for msg in reversed(mensagens):
        if isinstance(msg, HumanMessage):
            texto_usuario = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "human":
            texto_usuario = msg.get("content", "")
            break
        elif hasattr(msg, "content") and hasattr(msg, "type") and msg.type == "human":
            texto_usuario = msg.content
            break

    if not texto_usuario:
        return {
            "validacao_ok": False,
            "erros": [{"nó": "validacao", "erro": "Nenhuma mensagem do usuário encontrada."}],
        }

    # Verificar se é uma consulta de clima direta (sem código de reserva)
    eh_clima_direta, aeroporto_clima = _eh_consulta_clima_direta(texto_usuario)
    if eh_clima_direta and aeroporto_clima:
        if aeroporto_clima == "DESTINO_MEMORIA":
            # Usar destino da memória (estado anterior)
            status_voo_anterior = state.get("status_voo", {})
            destino_memoria = status_voo_anterior.get("destino", "")
            if destino_memoria:
                return {
                    "validacao_ok": True,
                    "codigo_reserva": state.get("codigo_reserva", ""),
                    "mensagem_usuario": texto_usuario,
                    "status_voo": status_voo_anterior,
                    "erros": [],
                }
            # Se não tem destino na memória, tentar usar codigo_reserva da memória
            codigo_anterior = state.get("codigo_reserva", "")
            if codigo_anterior:
                return {
                    "validacao_ok": True,
                    "codigo_reserva": codigo_anterior,
                    "mensagem_usuario": texto_usuario,
                    "erros": [],
                }
            # Sem destino e sem código — pedir informação
            return {
                "validacao_ok": False,
                "erros": [{"nó": "validacao", "erro": (
                    "Para consultar a previsão do tempo no destino, preciso saber "
                    "o código da sua reserva ou o nome da cidade.\n\n"
                    "Exemplos:\n"
                    "- `ABC123 previsão do tempo no destino`\n"
                    "- `previsão do tempo em São Paulo`"
                )}],
                "codigo_reserva": "",
                "mensagem_usuario": texto_usuario,
            }
        else:
            # Cidade específica encontrada — pular validação de código
            return {
                "validacao_ok": True,
                "codigo_reserva": state.get("codigo_reserva", ""),
                "mensagem_usuario": texto_usuario,
                "status_voo": {"destino": aeroporto_clima, "origem": "", "status": "consulta_clima_direta"},
                "erros": [],
            }

    # Verificar se é uma pergunta sobre voo sem código de reserva
    eh_sobre_voo = _eh_pergunta_sobre_voo(texto_usuario)

    # Extrair código de reserva da mensagem atual
    codigo = _extrair_codigo_reserva(texto_usuario)
    mensagem = _extrair_mensagem(texto_usuario, codigo) if codigo else texto_usuario

    # Validar código de reserva
    codigo_valido, erro_codigo = validar_codigo_reserva(codigo)
    if not codigo_valido:
        # Tentar usar código da sessão anterior (memória do checkpointer)
        codigo_anterior = state.get("codigo_reserva", "")
        if codigo_anterior:
            codigo_anterior_valido, _ = validar_codigo_reserva(codigo_anterior)
            if codigo_anterior_valido:
                # Usar código da memória — o usuário já informou antes
                codigo = codigo_anterior
                mensagem = texto_usuario
                codigo_valido = True

    if not codigo_valido:
        # Se é uma pergunta sobre voo e não tem código válido nem na memória, pedir
        if eh_sobre_voo:
            erro_msg_voo = (
                "Para consultar informações sobre seu voo, preciso do código de reserva "
                "(6 caracteres alfanuméricos, ex: ABC123).\n\n"
                "Por favor, envie sua mensagem no formato:\n"
                "**<código_reserva> <sua pergunta>**\n\n"
                "Exemplo: `ABC123 qual o status do meu voo?`"
            )
            return {
                "validacao_ok": False,
                "erros": [{"nó": "validacao", "erro": erro_msg_voo}],
                "codigo_reserva": state.get("codigo_reserva", ""),
                "mensagem_usuario": texto_usuario,
            }
        erros.append({"nó": "validacao", "erro": erro_codigo})
        return {
            "validacao_ok": False,
            "erros": erros,
            "codigo_reserva": state.get("codigo_reserva", ""),
            "mensagem_usuario": mensagem,
        }

    # Validar mensagem
    msg_valida, erro_msg = validar_mensagem(mensagem)
    if not msg_valida:
        erros.append({"nó": "validacao", "erro": erro_msg})
        return {
            "validacao_ok": False,
            "erros": erros,
            "codigo_reserva": codigo,
            "mensagem_usuario": mensagem,
        }

    # Verificar domínio
    dominio_ok, erro_dominio = verificar_dominio(mensagem)
    if not dominio_ok:
        erros.append({"nó": "validacao", "erro": erro_dominio})
        return {
            "validacao_ok": False,
            "erros": erros,
            "codigo_reserva": codigo,
            "mensagem_usuario": mensagem,
        }

    return {
        "validacao_ok": True,
        "codigo_reserva": codigo,
        "mensagem_usuario": mensagem,
        "erros": [],
    }


def consulta_voo_node(state: EstadoCrise) -> dict:
    """Nó de consulta de voo: consulta status pelo código de reserva."""
    try:
        codigo = state.get("codigo_reserva", "")
        # Se não há código de reserva (ex: consulta de clima direta), pular
        if not codigo:
            return {}
        resultado = consultar_status_voo.invoke({"codigo_reserva": codigo})
        dados_voo = _parse_status_voo(resultado)
        return {"status_voo": dados_voo}
    except Exception as e:
        return {
            "erros": state.get("erros", []) + [
                {"nó": "consulta_voo", "erro": str(e), "tipo": type(e).__name__}
            ]
        }


def consulta_clima_node(state: EstadoCrise) -> dict:
    """Nó de consulta climática: consulta clima do destino."""
    try:
        status_voo = state.get("status_voo", {})
        destino = status_voo.get("destino", "")
        if not destino:
            return {
                "info_clima": {"erro": "Destino não disponível para consulta climática."}
            }
        resultado = consultar_clima.invoke({"codigo_aeroporto": destino})
        dados_clima = _parse_clima(resultado)
        return {"info_clima": dados_clima}
    except Exception as e:
        return {
            "erros": state.get("erros", []) + [
                {"nó": "consulta_clima", "erro": str(e), "tipo": type(e).__name__}
            ]
        }


def consulta_transporte_node(state: EstadoCrise) -> dict:
    """Nó de consulta de transporte alternativo: busca opções entre origem e destino."""
    try:
        status_voo = state.get("status_voo", {})
        origem = status_voo.get("origem", "")
        destino = status_voo.get("destino", "")
        if not origem or not destino:
            return {
                "alternativas_transporte": ["Dados de origem/destino indisponíveis."]
            }
        resultado = consultar_transporte_alternativo.invoke(
            {"origem": origem, "destino": destino}
        )
        opcoes = _parse_transporte(resultado)
        return {"alternativas_transporte": opcoes}
    except Exception as e:
        return {
            "erros": state.get("erros", []) + [
                {"nó": "consulta_transporte", "erro": str(e), "tipo": type(e).__name__}
            ]
        }


def rag_node(state: EstadoCrise) -> dict:
    """Nó RAG: recupera políticas e direitos do passageiro relevantes."""
    try:
        busca = BuscaSemantica(DOCUMENTOS_POLITICAS)

        # Construir query baseada na situação
        status_voo = state.get("status_voo", {})
        mensagem = state.get("mensagem_usuario", "")
        status = status_voo.get("status", "")
        motivo = status_voo.get("motivo", "")

        query = f"{mensagem} {status} {motivo}".strip()
        if not query:
            query = "cancelamento voo direitos passageiro"

        resultados = busca.buscar(query, top_k=5)

        # Separar em políticas e direitos
        politicas = [
            doc for doc in resultados
            if doc.get("categoria") in ("reembolso", "reacomodacao", "assistencia", "overbooking", "bagagem", "clima")
        ]
        direitos = [
            doc for doc in resultados
            if doc.get("categoria") in ("direitos", "compensacao")
        ]

        # Se não houve separação significativa, usar todos em ambos
        if not politicas and resultados:
            politicas = resultados
        if not direitos and resultados:
            direitos = [doc for doc in resultados if doc.get("categoria") in ("direitos", "compensacao")]

        return {
            "politicas_recuperadas": politicas,
            "direitos_passageiro": direitos,
        }
    except Exception as e:
        return {
            "erros": state.get("erros", []) + [
                {"nó": "rag", "erro": str(e), "tipo": type(e).__name__}
            ]
        }


def analise_llm_node(state: EstadoCrise) -> dict:
    """Nó de análise LLM: envia dados coletados para análise contextual."""
    try:
        status_voo = state.get("status_voo", {})
        info_clima = state.get("info_clima", {})
        alternativas = state.get("alternativas_transporte", [])
        politicas = state.get("politicas_recuperadas", [])
        direitos = state.get("direitos_passageiro", [])
        mensagem_usuario = state.get("mensagem_usuario", "")
        erros_anteriores = state.get("erros", [])

        system_prompt = (
            "Você é um assistente especializado em gestão de crises de itinerários de viagem. "
            "Analise os dados coletados sobre a situação do viajante e prepare uma síntese "
            "para a geração do plano de contingência. "
            "Identifique os pontos críticos, os direitos aplicáveis e as melhores alternativas. "
            "Responda em português do Brasil de forma clara e objetiva."
        )

        dados_contexto = (
            f"SITUAÇÃO DO VIAJANTE: {mensagem_usuario}\n\n"
            f"STATUS DO VOO: {status_voo}\n\n"
            f"CONDIÇÕES CLIMÁTICAS: {info_clima}\n\n"
            f"ALTERNATIVAS DE TRANSPORTE: {alternativas}\n\n"
            f"POLÍTICAS APLICÁVEIS: {[p.get('titulo', '') + ': ' + p.get('conteudo', '') for p in politicas]}\n\n"
            f"DIREITOS DO PASSAGEIRO: {[d.get('titulo', '') + ': ' + d.get('conteudo', '') for d in direitos]}\n\n"
            f"ERROS DURANTE COLETA: {erros_anteriores}"
        )

        mensagens_llm = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=dados_contexto),
        ]

        resposta = _get_llm().invoke(mensagens_llm)

        return {
            "messages": [AIMessage(content=resposta.content)],
        }
    except Exception as e:
        return {
            "erros": state.get("erros", []) + [
                {"nó": "analise_llm", "erro": str(e), "tipo": type(e).__name__}
            ]
        }


def _eh_pergunta_simples(mensagem: str) -> bool:
    """Detecta se a mensagem do usuário é uma pergunta simples sobre o voo.

    Perguntas simples são consultas informativas (horário, destino, status)
    que NÃO envolvem uma situação de crise que exija plano completo.
    """
    mensagem_lower = mensagem.lower()

    # Padrões de perguntas simples/informativas
    padroes_simples = [
        r"qual\s+(é|e)?\s*(a|o)\s+(data|hora|horário|horario|destino|origem|status|situação|situacao|previsão|previsao|clima|tempo)",
        r"quando\s+(sai|parte|chega|decola|pousa)",
        r"que\s+horas?\s+(sai|parte|chega|é|e)",
        r"para\s+onde\s+vai",
        r"de\s+onde\s+(sai|parte)",
        r"me\s+(diga|informe|fale)\s+(sobre|o|a|os|as)",
        r"informações?\s+(do|sobre|da)\s+(meu|minha)?\s*(voo|reserva|viagem)",
        r"dados?\s+(do|da)\s+(meu|minha)?\s*(voo|reserva)",
        r"previsão\s+(do|de)\s+tempo",
        r"previsao\s+(do|de)\s+tempo",
        r"como\s+(está|esta|tá|ta)\s+(o\s+)?(clima|tempo)",
        r"clima\s+(no|do|em|na)",
        r"tempo\s+(no|do|em|na)",
        r"temperatura\s+(no|do|em|na)",
        r"condições?\s+(climática|climatica|meteorológica|meteorologica)",
        r"(data|hora|horário|horario)\s+(do|da|de)\s+(meu|minha)?\s*(voo|viagem|reserva|partida|chegada)",
        r"qual\s+(a|o)\s+(data|hora|horário|horario)",
    ]

    # Padrões que indicam CRISE (deve gerar plano completo)
    padroes_crise = [
        r"cancelad[oa]", r"atrasad[oa]", r"perd[ie]",
        r"não\s+consigo", r"nao\s+consigo", r"preciso\s+de\s+ajuda",
        r"o\s+que\s+(fazer|faço|faco)", r"meus\s+direitos",
        r"reembols", r"compensaç", r"alternativ",
        r"conexão\s+perdida", r"conexao\s+perdida",
        r"emergência", r"emergencia", r"urgente",
    ]

    # Se contém padrão de crise, NÃO é pergunta simples
    for padrao in padroes_crise:
        if re.search(padrao, mensagem_lower):
            return False

    # Se contém padrão de pergunta simples, É pergunta simples
    for padrao in padroes_simples:
        if re.search(padrao, mensagem_lower):
            return True

    # Se a mensagem é curta e termina com ?, provavelmente é pergunta simples
    if mensagem.strip().endswith("?") and len(mensagem.split()) <= 15:
        return True

    return False


def gerar_plano_node(state: EstadoCrise) -> dict:
    """Nó de geração do plano de contingência em Markdown.

    Se o usuário fez uma pergunta simples (ex: 'qual a data do meu voo?'),
    responde diretamente com a informação solicitada.
    Se envolve uma crise, gera o plano completo com 5 seções.
    """
    try:
        status_voo = state.get("status_voo", {})
        info_clima = state.get("info_clima", {})
        alternativas = state.get("alternativas_transporte", [])
        politicas = state.get("politicas_recuperadas", [])
        direitos = state.get("direitos_passageiro", [])
        mensagem_usuario = state.get("mensagem_usuario", "")
        erros = state.get("erros", [])

        # Verificar se é uma pergunta simples ou uma situação de crise
        if _eh_pergunta_simples(mensagem_usuario):
            return _gerar_resposta_direta(state)

        # --- MODO PLANO COMPLETO (situação de crise) ---

        # Identificar seções com dados indisponíveis
        secoes_parciais = []
        if not status_voo:
            secoes_parciais.append("Status do Voo")
        if not info_clima or info_clima.get("erro"):
            secoes_parciais.append("Condições Climáticas")
        if not alternativas:
            secoes_parciais.append("Transporte Alternativo")
        if not politicas and not direitos:
            secoes_parciais.append("Políticas e Direitos")

        system_prompt = (
            "Você é um assistente especializado em gestão de crises de itinerários de viagem. "
            "Gere um plano de contingência personalizado em formato Markdown. "
            "O plano DEVE conter exatamente estas 5 seções com os cabeçalhos abaixo:\n"
            "## 1. Diagnóstico da Situação\n"
            "## 2. Direitos do Passageiro\n"
            "## 3. Opções de Reembolso\n"
            "## 4. Rotas Alternativas\n"
            "## 5. Recomendações Imediatas\n\n"
            "REGRAS OBRIGATÓRIAS:\n"
            "- Escreva em português do Brasil.\n"
            "- Use linguagem clara, sem jargão técnico.\n"
            "- Cada frase deve ter no máximo 30 palavras.\n"
            "- Referencie dados específicos do viajante (número do voo, destino, horários, condições) "
            "em pelo menos 3 das 5 seções.\n"
            "- Se alguma informação estiver indisponível, indique explicitamente na seção correspondente "
            "que os dados não puderam ser obtidos.\n"
            "- Use bullet points para facilitar a leitura.\n"
            "- NÃO inclua cabeçalho de nível 1 (# título). Comece direto com as seções ##."
        )

        info_parcial = ""
        if secoes_parciais:
            info_parcial = (
                f"\n\nATENÇÃO: As seguintes fontes de dados NÃO retornaram informações: "
                f"{', '.join(secoes_parciais)}. Indique isso explicitamente nas seções afetadas."
            )

        dados_contexto = (
            f"SITUAÇÃO DO VIAJANTE: {mensagem_usuario}\n\n"
            f"STATUS DO VOO:\n"
            f"  Número: {status_voo.get('voo', 'Indisponível')}\n"
            f"  Origem: {status_voo.get('origem', 'Indisponível')}\n"
            f"  Destino: {status_voo.get('destino', 'Indisponível')}\n"
            f"  Partida: {status_voo.get('partida', 'Indisponível')}\n"
            f"  Chegada: {status_voo.get('chegada', 'Indisponível')}\n"
            f"  Status: {status_voo.get('status', 'Indisponível')}\n"
            f"  Motivo: {status_voo.get('motivo', 'Indisponível')}\n\n"
            f"CONDIÇÕES CLIMÁTICAS: {info_clima.get('texto_completo', 'Indisponível')}\n\n"
            f"ALTERNATIVAS DE TRANSPORTE: {chr(10).join(str(a) for a in alternativas) if alternativas else 'Nenhuma encontrada'}\n\n"
            f"POLÍTICAS APLICÁVEIS:\n"
            f"{chr(10).join(p.get('titulo', '') + ': ' + p.get('conteudo', '') for p in politicas) if politicas else 'Nenhuma recuperada'}\n\n"
            f"DIREITOS DO PASSAGEIRO:\n"
            f"{chr(10).join(d.get('titulo', '') + ': ' + d.get('conteudo', '') for d in direitos) if direitos else 'Nenhum recuperado'}"
            f"{info_parcial}"
        )

        mensagens_llm = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=dados_contexto),
        ]

        resposta = _get_llm().invoke(mensagens_llm)

        return {
            "relatorio_final": resposta.content,
            "messages": [AIMessage(content=resposta.content)],
        }
    except Exception as e:
        # Se a geração falhar, retorna mensagem de erro
        erro_msg = (
            "## Erro na Geração do Plano\n\n"
            "Não foi possível gerar o plano de contingência completo. "
            f"Motivo: {str(e)}\n\n"
            "Por favor, tente novamente em alguns instantes."
        )
        return {
            "relatorio_final": erro_msg,
            "erros": state.get("erros", []) + [
                {"nó": "gerar_plano", "erro": str(e), "tipo": type(e).__name__}
            ],
        }


def _gerar_resposta_direta(state: EstadoCrise) -> dict:
    """Gera uma resposta direta e concisa para perguntas simples do usuário.

    Em vez de gerar o plano completo de 5 seções, responde apenas o que
    foi perguntado usando os dados coletados do estado.
    """
    try:
        status_voo = state.get("status_voo", {})
        info_clima = state.get("info_clima", {})
        alternativas = state.get("alternativas_transporte", [])
        mensagem_usuario = state.get("mensagem_usuario", "")

        system_prompt = (
            "Você é um assistente de viagens. O usuário fez uma pergunta simples "
            "sobre seu voo ou itinerário. Responda APENAS o que foi perguntado, "
            "de forma direta e concisa. Use os dados disponíveis abaixo.\n\n"
            "REGRAS:\n"
            "- Responda em português do Brasil.\n"
            "- Seja direto — responda SOMENTE o que foi perguntado.\n"
            "- NÃO gere um plano de contingência completo.\n"
            "- NÃO inclua seções ## ou cabeçalhos.\n"
            "- Se a informação solicitada não estiver disponível, diga claramente.\n"
            "- Formate de forma limpa e legível."
        )

        dados_contexto = (
            f"PERGUNTA DO USUÁRIO: {mensagem_usuario}\n\n"
            f"DADOS DO VOO DISPONÍVEIS:\n"
            f"  Número do voo: {status_voo.get('voo', 'Indisponível')}\n"
            f"  Origem: {status_voo.get('origem', 'Indisponível')}\n"
            f"  Destino: {status_voo.get('destino', 'Indisponível')}\n"
            f"  Partida: {status_voo.get('partida', 'Indisponível')}\n"
            f"  Chegada: {status_voo.get('chegada', 'Indisponível')}\n"
            f"  Status: {status_voo.get('status', 'Indisponível')}\n"
            f"  Motivo: {status_voo.get('motivo', 'N/A')}\n\n"
            f"CLIMA NO DESTINO: {info_clima.get('texto_completo', 'Indisponível')}\n\n"
            f"TRANSPORTE ALTERNATIVO: {chr(10).join(str(a) for a in alternativas) if alternativas else 'Não consultado'}"
        )

        mensagens_llm = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=dados_contexto),
        ]

        resposta = _get_llm().invoke(mensagens_llm)

        return {
            "relatorio_final": resposta.content,
            "messages": [AIMessage(content=resposta.content)],
        }
    except Exception as e:
        erro_msg = f"Não foi possível processar sua pergunta. Motivo: {str(e)}"
        return {
            "relatorio_final": erro_msg,
            "erros": state.get("erros", []) + [
                {"nó": "gerar_plano", "erro": str(e), "tipo": type(e).__name__}
            ],
        }


def erro_node(state: EstadoCrise) -> dict:
    """Nó de erro: gera mensagem amigável baseada nos erros registrados."""
    erros = state.get("erros", [])

    if erros:
        # Pegar o último erro relevante para mostrar ao usuário
        ultimo_erro = erros[-1] if erros else {}
        mensagem_erro = ultimo_erro.get("erro", "Ocorreu um erro não identificado.")
    else:
        mensagem_erro = "Ocorreu um erro durante o processamento da sua solicitação."

    relatorio = (
        "## Não foi possível processar sua solicitação\n\n"
        f"{mensagem_erro}\n\n"
        "### O que você pode fazer:\n"
        "- Verifique se o código de reserva está correto (6 caracteres, ex: ABC123).\n"
        "- Descreva sua situação de viagem com mais detalhes.\n"
        "- Certifique-se de incluir informações sobre seu voo, reserva ou itinerário.\n"
        "- Tente novamente em alguns instantes."
    )

    return {
        "relatorio_final": relatorio,
        "messages": [AIMessage(content=relatorio)],
    }


# ---------------------------------------------------------------------------
# Roteador condicional
# ---------------------------------------------------------------------------

def roteador_validacao(state: EstadoCrise) -> str:
    """Aresta condicional: direciona fluxo baseado no resultado da validação."""
    if state.get("validacao_ok", False):
        return "consulta_voo"
    return "erro"


# ---------------------------------------------------------------------------
# Construção do grafo
# ---------------------------------------------------------------------------

def build_graph():
    """Constrói e compila o StateGraph do agente de gestão de crises.

    Returns:
        CompiledGraph pronto para invocação com MemorySaver como checkpointer.
    """
    graph = StateGraph(EstadoCrise)

    # Registrar todos os 8 nós
    graph.add_node("validacao", validacao_node)
    graph.add_node("consulta_voo", consulta_voo_node)
    graph.add_node("consulta_clima", consulta_clima_node)
    graph.add_node("consulta_transporte", consulta_transporte_node)
    graph.add_node("rag", rag_node)
    graph.add_node("analise_llm", analise_llm_node)
    graph.add_node("gerar_plano", gerar_plano_node)
    graph.add_node("erro", erro_node)

    # Aresta inicial: START → validação
    graph.add_edge(START, "validacao")

    # Aresta condicional: validação → consulta_voo (ok) ou erro (falha)
    graph.add_conditional_edges("validacao", roteador_validacao)

    # Arestas sequenciais do fluxo principal
    graph.add_edge("consulta_voo", "consulta_clima")
    graph.add_edge("consulta_clima", "consulta_transporte")
    graph.add_edge("consulta_transporte", "rag")
    graph.add_edge("rag", "analise_llm")
    graph.add_edge("analise_llm", "gerar_plano")
    graph.add_edge("gerar_plano", END)

    # Aresta do nó de erro para o fim
    graph.add_edge("erro", END)

    # Compilar com checkpointer de memória
    return graph.compile(checkpointer=MemorySaver())
