"""
Estado compartilhado do agente de gestão de crises em itinerários.

Define o TypedDict que flui por todos os nós do grafo LangGraph,
mantendo os dados coletados durante a execução do fluxo.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class EstadoCrise(TypedDict):
    """Estado compartilhado entre todos os nós do grafo de gestão de crises.

    Cada campo é inicializável com valor vazio correspondente ao seu tipo:
    - str → ""
    - dict → {}
    - list → []
    - bool → False

    Campos com Annotated[..., operator.add] usam reducer de acumulação,
    permitindo que nós paralelos acumulem valores sem sobrescrever.
    """

    messages: Annotated[list, add_messages]  # Histórico de mensagens (chat)
    codigo_reserva: str  # Código de reserva validado (6 caracteres A-Z0-9)
    mensagem_usuario: str  # Descrição da crise pelo viajante
    dados_cliente: dict  # Informações extraídas do cliente
    status_voo: dict  # Resultado da consulta de status do voo
    info_clima: dict  # Resultado da consulta climática
    alternativas_transporte: list  # Opções de transporte alternativo
    politicas_recuperadas: list  # Documentos RAG de políticas da empresa
    direitos_passageiro: list  # Documentos RAG de legislação de direitos
    relatorio_final: str  # Plano de contingência gerado em Markdown
    erros: Annotated[list, operator.add]  # Erros acumulados (reducer para paralelização)
    validacao_ok: bool  # Flag indicando se a validação foi aprovada
