"""
Interface web Gradio para o agente de gestão de crises em itinerários de viagem.

v1.1: Suporte a múltiplas sessões simultâneas, histórico persistente,
visualização do grafo em tempo real e confirmação pós-atendimento.

Fornece uma interface de chat onde o usuário pode informar seu código de reserva
e descrever sua situação de crise para receber um plano de contingência.
"""

import time
import uuid

import gradio as gr
from langchain_core.messages import HumanMessage

from src.agente import build_graph
from src.persistencia import get_gerenciador


# Instância do grafo compilado (singleton)
_graph = None


def _get_graph():
    """Retorna o grafo compilado, inicializando apenas na primeira chamada."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _gerar_thread_id() -> str:
    """Gera um thread_id único por sessão de usuário."""
    return f"gradio-{uuid.uuid4().hex[:12]}"


def _criar_grafo_visual(etapa_atual: str = "") -> str:
    """Cria representação visual do grafo em Markdown mostrando a etapa atual.

    Args:
        etapa_atual: Nome do nó sendo executado.

    Returns:
        String Markdown com o grafo visual.
    """
    etapas = [
        ("validacao", "Validação"),
        ("consulta_voo", "Consulta Voo"),
        ("consulta_clima", "Consulta Clima"),
        ("consulta_transporte", "Transporte"),
        ("rag", "RAG - Políticas"),
        ("analise_llm", "Análise LLM"),
        ("gerar_plano", "Gerar Plano"),
    ]

    linhas = ["**Fluxo do Agente:**\n"]
    for key, label in etapas:
        if key == etapa_atual:
            linhas.append(f"  **▶ {label}** ⏳")
        elif etapas.index((key, label)) < [i for i, (k, _) in enumerate(etapas) if k == etapa_atual][0] if etapa_atual and etapa_atual in [k for k, _ in etapas] else -1:
            linhas.append(f"  ✅ {label}")
        else:
            linhas.append(f"  ○ {label}")

    return "\n".join(linhas)


def responder(mensagem: str, historico: list, request: gr.Request = None) -> str:
    """Processa a mensagem do usuário e retorna a resposta do agente.

    Cada sessão de navegador recebe um thread_id único, permitindo
    múltiplas sessões simultâneas com memória independente.

    Args:
        mensagem: Texto do usuário contendo código de reserva e descrição da crise.
        historico: Histórico de mensagens da conversa (formato Gradio).
        request: Objeto de request do Gradio com informações da sessão.

    Returns:
        Resposta do agente com o plano de contingência ou mensagem de erro amigável.
    """
    if not mensagem or not mensagem.strip():
        return (
            "Por favor, envie uma mensagem com seu código de reserva "
            "(6 caracteres, ex: ABC123) e a descrição da sua situação de viagem."
        )

    # Gerar thread_id único por sessão (baseado no hash do session_hash do Gradio)
    session_hash = ""
    if request:
        session_hash = request.session_hash or ""

    if session_hash:
        thread_id = f"gradio-{session_hash[:12]}"
    else:
        # Fallback: usar hash do histórico para manter consistência
        thread_id = f"gradio-{hash(str(len(historico))) % 10**8:08d}"

    # Registrar sessão no gerenciador de persistência
    gerenciador = get_gerenciador()
    gerenciador.criar_sessao(thread_id)

    # Registrar mensagem do usuário
    gerenciador.registrar_interacao(thread_id, "human", mensagem)

    config = {"configurable": {"thread_id": thread_id}}

    inicio = time.time()

    try:
        resultado = _get_graph().invoke(
            {"messages": [HumanMessage(content=mensagem)]},
            config,
        )

        tempo_ms = int((time.time() - inicio) * 1000)

        # Priorizar o relatório final; fallback para a última mensagem
        relatorio = resultado.get("relatorio_final", "")
        if relatorio:
            resposta_final = relatorio
        else:
            # Fallback: extrair conteúdo da última mensagem AI
            mensagens = resultado.get("messages", [])
            if mensagens:
                ultima = mensagens[-1]
                if hasattr(ultima, "content"):
                    resposta_final = ultima.content
                elif isinstance(ultima, dict):
                    resposta_final = ultima.get("content", "")
                else:
                    resposta_final = "Não foi possível gerar uma resposta. Tente novamente."
            else:
                resposta_final = "Não foi possível gerar uma resposta. Tente novamente."

        # Adicionar confirmação de continuidade (v1.1)
        resposta_final += (
            "\n\n---\n"
            "💬 *Precisa de mais ajuda? Posso esclarecer algum ponto do plano, "
            "buscar mais alternativas ou verificar informações adicionais.*"
        )

        # Registrar resposta e analytics
        gerenciador.registrar_interacao(
            thread_id, "ai", resposta_final,
            metadata={"tempo_resposta_ms": tempo_ms}
        )
        gerenciador.registrar_evento_analytics(
            evento="resposta_gerada",
            thread_id=thread_id,
            dados={
                "tipo": "crise" if "##" in resposta_final else "simples",
                "codigo_reserva": resultado.get("codigo_reserva", ""),
            },
            tempo_resposta_ms=tempo_ms,
        )

        # Atualizar código de reserva na sessão se encontrado
        codigo = resultado.get("codigo_reserva", "")
        if codigo:
            gerenciador.atualizar_codigo_reserva(thread_id, codigo)

        return resposta_final

    except Exception as e:
        tempo_ms = int((time.time() - inicio) * 1000)
        gerenciador.registrar_evento_analytics(
            evento="erro",
            thread_id=thread_id,
            dados={"erro": str(e)[:200]},
            tempo_resposta_ms=tempo_ms,
        )
        return (
            "⚠️ Não foi possível processar sua solicitação no momento.\n\n"
            "**Possíveis causas:**\n"
            "- Serviço temporariamente indisponível\n"
            "- Erro de conexão com serviços externos\n\n"
            "**O que fazer:**\n"
            "- Verifique se sua mensagem contém o código de reserva (6 caracteres, ex: ABC123)\n"
            "- Descreva sua situação de viagem com detalhes\n"
            "- Tente novamente em alguns instantes\n\n"
            f"_Detalhes técnicos: {str(e)[:200]}_"
        )


def criar_interface_grafo():
    """Cria o componente de visualização do grafo do agente."""
    grafo_markdown = """
### Arquitetura do Agente

```
┌─────────────────────────────────────────────────────┐
│               INTERFACE (Gradio / CLI)                │
├─────────────────────────────────────────────────────┤
│                   AGENTE (LangGraph)                  │
│                                                       │
│  [Validação] → [Voo] → [Clima] → [Transporte]       │
│       ↓                                              │
│  [RAG] → [Análise LLM] → [Plano de Contingência]    │
│                                                       │
├─────────────────────────────────────────────────────┤
│          ESTADO (TypedDict + SQLite Persistence)      │
└─────────────────────────────────────────────────────┘
```

**Nós do Grafo:**
1. **Validação** — Extrai código de reserva e valida domínio
2. **Consulta Voo** — Busca status do voo na base de dados
3. **Consulta Clima** — API Open-Meteo para condições meteorológicas
4. **Transporte** — Alternativas de transporte (voo, ônibus, trem)
5. **RAG** — Recupera políticas e direitos do passageiro (TF-IDF)
6. **Análise LLM** — Síntese contextual com Llama 3.3 70B
7. **Gerar Plano** — Plano de contingência personalizado em Markdown
"""
    return grafo_markdown


# ---------------------------------------------------------------------------
# Configuração da interface Gradio (v1.1 — Multi-sessão + Visualização)
# ---------------------------------------------------------------------------

with gr.Blocks(
    title="Viagem Inteligente — Gestão de Crises",
) as demo:
    gr.Markdown(
        "# ✈️ Viagem Inteligente — Gestão de Crises em Itinerários\n"
        "Informe seu código de reserva (6 caracteres, ex: ABC123) "
        "e descreva sua situação de viagem."
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Conversa",
                height=500,
            )
            msg_input = gr.Textbox(
                placeholder="Ex: ABC123 Meu voo foi cancelado por mau tempo...",
                label="Sua mensagem",
                lines=1,
                show_label=False,
            )
            with gr.Row():
                enviar_btn = gr.Button("Enviar", variant="primary")
                limpar_btn = gr.Button("Nova Sessão", variant="secondary")

        with gr.Column(scale=1):
            gr.Markdown("### 📊 Fluxo do Agente")
            grafo_info = gr.Markdown(value=criar_interface_grafo())

            gr.Markdown("### 💡 Exemplos")
            gr.Markdown(
                "- `ABC123 Meu voo foi cancelado por mau tempo`\n"
                "- `MNO345 Preciso chegar a Porto Alegre urgente`\n"
                "- `DEF456 Voo atrasou mais de 4 horas`\n"
                "- `Previsão do tempo em Curitiba`\n"
                "- `Quais meus direitos?` (com sessão ativa)"
            )

    # Estado da sessão para multi-sessão
    session_state = gr.State(value={"thread_id": None})

    def _processar_mensagem(mensagem, historico, request: gr.Request):
        """Processa a mensagem e atualiza o chat."""
        if not mensagem or not mensagem.strip():
            return historico, ""

        # Adicionar mensagem do usuário ao histórico visual
        historico = historico or []
        historico.append({"role": "user", "content": mensagem})

        # Obter resposta do agente
        resposta = responder(mensagem, historico, request)

        # Adicionar resposta ao histórico visual
        historico.append({"role": "assistant", "content": resposta})

        return historico, ""

    def _limpar_sessao():
        """Inicia uma nova sessão (limpa histórico visual)."""
        return [], ""

    # Conectar eventos
    msg_input.submit(
        fn=_processar_mensagem,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input],
    )
    enviar_btn.click(
        fn=_processar_mensagem,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input],
    )
    limpar_btn.click(
        fn=_limpar_sessao,
        inputs=[],
        outputs=[chatbot, msg_input],
    )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, theme=gr.themes.Soft())
