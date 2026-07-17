"""
Interface web Gradio para o agente de gestão de crises em itinerários de viagem.

Fornece uma interface de chat onde o usuário pode informar seu código de reserva
e descrever sua situação de crise para receber um plano de contingência.
"""

import uuid

import gradio as gr
from langchain_core.messages import HumanMessage

from src.agente import build_graph


# Instância do grafo compilado (singleton)
_graph = None

# Thread ID fixo por sessão do servidor (simplificação para sessão única)
_SESSION_THREAD_ID = f"gradio-{uuid.uuid4().hex[:8]}"


def _get_graph():
    """Retorna o grafo compilado, inicializando apenas na primeira chamada."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def responder(mensagem: str, historico: list) -> str:
    """Processa a mensagem do usuário e retorna a resposta do agente.

    Args:
        mensagem: Texto do usuário contendo código de reserva e descrição da crise.
        historico: Histórico de mensagens da conversa (formato Gradio).

    Returns:
        Resposta do agente com o plano de contingência ou mensagem de erro amigável.
    """
    if not mensagem or not mensagem.strip():
        return (
            "Por favor, envie uma mensagem com seu código de reserva "
            "(6 caracteres, ex: ABC123) e a descrição da sua situação de viagem."
        )

    # Usar thread_id fixo para manter memória durante toda a sessão
    config = {"configurable": {"thread_id": _SESSION_THREAD_ID}}

    try:
        resultado = _get_graph().invoke(
            {"messages": [HumanMessage(content=mensagem)]},
            config,
        )

        # Priorizar o relatório final; fallback para a última mensagem
        relatorio = resultado.get("relatorio_final", "")
        if relatorio:
            return relatorio

        # Fallback: extrair conteúdo da última mensagem AI
        mensagens = resultado.get("messages", [])
        if mensagens:
            ultima = mensagens[-1]
            if hasattr(ultima, "content"):
                return ultima.content
            elif isinstance(ultima, dict):
                return ultima.get("content", "")

        return "Não foi possível gerar uma resposta. Tente novamente."

    except Exception as e:
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


# ---------------------------------------------------------------------------
# Configuração da interface Gradio
# ---------------------------------------------------------------------------

demo = gr.ChatInterface(
    fn=responder,
    title="✈️ Agente de Gestão de Crises — Itinerários de Viagem",
    description=(
        "Informe seu código de reserva (6 caracteres, ex: ABC123) "
        "e descreva sua situação de viagem. O agente irá consultar o status do voo, "
        "condições climáticas, opções de transporte alternativo e seus direitos como "
        "passageiro para gerar um plano de contingência personalizado."
    ),
    examples=[
        "ABC123 Meu voo foi cancelado por mau tempo e vou perder minha conexão para o Rio.",
        "MNO345 Meu voo está cancelado por neblina e preciso chegar a Porto Alegre urgente.",
        "DEF456 Estou no aeroporto de Brasília e meu voo atrasou mais de 4 horas.",
    ],
)


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
