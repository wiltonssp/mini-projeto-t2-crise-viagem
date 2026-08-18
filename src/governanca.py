"""
Módulo de segurança, governança e limites de autonomia.

Implementa:
- Detecção de prompt injection e entradas adversariais
- Limites de autonomia do agente
- Mecanismo de aprovação humana para ações sensíveis
- Sanitização de entradas não confiáveis
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Padrões de prompt injection conhecidos
# ---------------------------------------------------------------------------

_PADROES_INJECTION = [
    # Tentativas de substituir instruções do sistema
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignor[ea]\s+(todas?\s+)?(as\s+)?instru[cç][oõ]es\s+anteriores",
    r"esquec[ea]\s+(tudo|todas?\s+instru[cç][oõ]es)",
    r"disregard\s+(all\s+)?prior\s+(instructions|prompts)",
    r"override\s+(system|previous)\s+(prompt|instructions)",
    # Tentativas de revelar informações do sistema
    r"(show|reveal|display|print)\s+(me\s+)?(your|the)\s+(system\s+)?prompt",
    r"(mostre|revele|exiba)\s+(o\s+)?(seu\s+)?prompt\s+(de\s+sistema|interno)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(instructions|prompt|rules)",
    r"quais\s+s[aã]o\s+suas?\s+instru[cç][oõ]es",
    # Tentativas de mudar papel/identidade
    r"you\s+are\s+now\s+a",
    r"agora\s+voc[eê]\s+[eé]\s+um",
    r"act\s+as\s+(a|an)\s+",
    r"atue\s+como\s+",
    r"pretend\s+(you\s+are|to\s+be)",
    r"finja\s+(ser|que\s+[eé])",
    # Tentativas de executar código ou acessar sistema
    r"(execute|run|eval)\s*(this\s+)?code",
    r"(execut[ea]|rod[ea])\s*(este\s+)?c[oó]digo",
    r"import\s+os|subprocess|exec\(|eval\(",
    r"(access|read|write)\s+(file|database|system)",
    r"(acess[ea]|l[eê]|escrev[ea])\s+(arquivo|banco|sistema)",
    # Tentativas de exfiltrar dados
    r"(send|transmit|post)\s+(data|info|credentials)\s+to",
    r"(envi[ea]|transmit[ea])\s+(dados|credenciais)\s+para",
    r"(api.?key|senha|password|secret|token)",
    # Delimitadores de injeção
    r"```\s*(system|assistant|hidden)",
    r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>",
    r"<<\s*SYS\s*>>|<<\s*/SYS\s*>>",
]

# Compilar padrões uma vez
_REGEX_INJECTION = [re.compile(p, re.IGNORECASE) for p in _PADROES_INJECTION]

# ---------------------------------------------------------------------------
# Ações que requerem aprovação humana
# ---------------------------------------------------------------------------

_ACOES_SENSIVEIS = [
    "cancelar_reserva",
    "solicitar_reembolso",
    "alterar_voo",
    "compartilhar_dados_pessoais",
]


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------


def detectar_prompt_injection(texto: str) -> tuple[bool, Optional[str]]:
    """Detecta tentativas de prompt injection na entrada do usuário.

    Args:
        texto: Texto de entrada do usuário.

    Returns:
        Tupla (is_injection, motivo).
        - (True, "motivo") se detectou injection
        - (False, None) se entrada é segura
    """
    if not texto:
        return False, None

    texto_normalizado = texto.lower().strip()

    for regex in _REGEX_INJECTION:
        match = regex.search(texto_normalizado)
        if match:
            padrao_detectado = match.group(0)
            motivo = f"Padrão adversarial detectado: '{padrao_detectado}'"
            logger.warning(
                "SEGURANCA: Prompt injection detectado | "
                "padrao='%s' | input_length=%d",
                padrao_detectado, len(texto)
            )
            return True, motivo

    # Heurísticas adicionais
    # 1. Excesso de delimitadores especiais (tentativa de confundir parser)
    delimitadores = texto.count("```") + texto.count("---") + texto.count("===")
    if delimitadores > 3:
        motivo = "Excesso de delimitadores especiais detectado"
        logger.warning("SEGURANCA: %s | count=%d", motivo, delimitadores)
        return True, motivo

    # 2. Texto muito longo com instruções embutidas (> 2000 chars)
    if len(texto) > 2000 and any(
        kw in texto_normalizado for kw in [
            "instruction", "instrução", "system prompt", "you must",
            "você deve ignorar", "new task"
        ]
    ):
        motivo = "Texto excessivamente longo com instruções embutidas suspeitas"
        logger.warning("SEGURANCA: %s | length=%d", motivo, len(texto))
        return True, motivo

    return False, None


def verificar_limites_autonomia(acao: str) -> dict:
    """Verifica se uma ação está dentro dos limites de autonomia do agente.

    O agente é somente leitura — ações destrutivas/irreversíveis são bloqueadas
    ou condicionadas à aprovação humana.

    Args:
        acao: Nome da ação que o agente pretende executar.

    Returns:
        Dict com:
        - permitido (bool): Se a ação pode ser executada
        - requer_aprovacao (bool): Se precisa de confirmação humana
        - motivo (str): Explicação da decisão
    """
    acao_lower = acao.lower().strip()

    # Ações completamente bloqueadas (destrutivas)
    acoes_bloqueadas = [
        "deletar", "excluir", "drop", "delete",
        "alterar_sistema", "modificar_config",
    ]
    for bloqueada in acoes_bloqueadas:
        if bloqueada in acao_lower:
            logger.warning(
                "GOVERNANCA: Ação bloqueada | acao='%s'", acao
            )
            return {
                "permitido": False,
                "requer_aprovacao": False,
                "motivo": f"Ação '{acao}' bloqueada — operações destrutivas não são permitidas.",
            }

    # Ações que requerem aprovação humana
    if acao_lower in _ACOES_SENSIVEIS:
        logger.info(
            "GOVERNANCA: Ação requer aprovação humana | acao='%s'", acao
        )
        return {
            "permitido": True,
            "requer_aprovacao": True,
            "motivo": (
                f"A ação '{acao}' requer confirmação do usuário antes de ser executada. "
                "Deseja prosseguir?"
            ),
        }

    # Ações de consulta — sempre permitidas
    return {
        "permitido": True,
        "requer_aprovacao": False,
        "motivo": "Ação de consulta — dentro dos limites de autonomia.",
    }


def sanitizar_entrada(texto: str) -> str:
    """Sanitiza a entrada do usuário removendo caracteres potencialmente perigosos.

    Mantém o texto legível mas remove tentativas de injeção de markup/código.

    Args:
        texto: Texto bruto do usuário.

    Returns:
        Texto sanitizado.
    """
    # Remover tokens de controle de LLM
    texto = re.sub(r'<\|[^|]*\|>', '', texto)
    texto = re.sub(r'\[INST\]|\[/INST\]', '', texto)
    texto = re.sub(r'<<\s*/?SYS\s*>>', '', texto)

    # Remover tentativas de injeção via markdown de código com role
    texto = re.sub(r'```\s*(system|assistant|hidden)[^`]*```', '', texto, flags=re.DOTALL)

    return texto.strip()


def gerar_resposta_bloqueio() -> str:
    """Gera mensagem padrão quando uma entrada é bloqueada por segurança.

    Returns:
        Mensagem amigável informando o bloqueio.
    """
    return (
        "Sua mensagem foi bloqueada por nosso sistema de segurança.\n\n"
        "Este agente é especializado em **gestão de crises em itinerários de viagem**. "
        "Posso ajudar com:\n"
        "- Status de voos e reservas\n"
        "- Previsão do tempo no destino\n"
        "- Direitos do passageiro\n"
        "- Planos de contingência para cancelamentos e atrasos\n\n"
        "Por favor, reformule sua pergunta dentro do contexto de viagem."
    )
