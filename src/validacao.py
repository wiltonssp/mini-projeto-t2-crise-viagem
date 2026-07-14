"""
Módulo de validação de entrada do usuário.

Valida código de reserva, mensagem do viajante e pertinência ao domínio
de crises em itinerários de viagem.
"""

import re


def validar_codigo_reserva(codigo: str) -> tuple[bool, str]:
    """Valida código de reserva: 6 caracteres alfanuméricos A-Z0-9.

    Args:
        codigo: Código de reserva fornecido pelo usuário.

    Returns:
        Tupla (True, "") se válido, ou (False, mensagem_erro) se inválido.
    """
    pattern = r'^[A-Z0-9]{6}$'
    if re.match(pattern, codigo):
        return True, ""
    return False, (
        "Código de reserva inválido. O formato esperado é "
        "alfanumérico com exatamente 6 caracteres (ex: XYZ123)."
    )


def validar_mensagem(mensagem: str) -> tuple[bool, str]:
    """Valida mensagem do usuário: 10-2000 caracteres não-espaço.

    Rejeita strings vazias ou compostas apenas por espaços em branco.

    Args:
        mensagem: Mensagem descrevendo a situação de crise do viajante.

    Returns:
        Tupla (True, "") se válida, ou (False, mensagem_erro) se inválida.
    """
    chars_nao_espaco = len(mensagem.replace(" ", "").replace("\t", "").replace("\n", ""))
    if chars_nao_espaco == 0:
        return False, "Por favor, forneça uma descrição válida da sua situação."
    if chars_nao_espaco < 10:
        return False, (
            "Descreva sua situação com mais detalhes. "
            "Mínimo de 10 caracteres necessário."
        )
    if len(mensagem) > 2000:
        return False, "Mensagem muito longa. Máximo de 2000 caracteres."
    return True, ""


# Palavras-chave do domínio de crises em itinerários de viagem
PALAVRAS_CHAVE_DOMINIO = [
    "viagem", "voo", "aeroporto", "conexão", "conexao",
    "itinerário", "itinerario", "reserva", "bagagem",
    "transporte", "clima", "cancelado", "cancelamento",
    "atraso", "atrasado", "embarque", "escala", "mala",
    "passagem", "passageiro", "companhia", "aerea", "aérea",
]


def verificar_dominio(mensagem: str) -> tuple[bool, str]:
    """Verifica se a mensagem está relacionada ao domínio de crises de viagem.

    Busca presença de pelo menos uma palavra-chave do domínio na mensagem.

    Args:
        mensagem: Mensagem do usuário para verificação de pertinência.

    Returns:
        Tupla (True, "") se pertinente ao domínio, ou (False, mensagem_erro)
        se a mensagem não contém palavras-chave de viagem.
    """
    mensagem_lower = mensagem.lower()
    for palavra in PALAVRAS_CHAVE_DOMINIO:
        if palavra in mensagem_lower:
            return True, ""
    return False, (
        "Desculpe, só posso ajudar com situações relacionadas a "
        "itinerários de viagem. Por favor, reformule sua mensagem "
        "incluindo detalhes sobre seu voo, reserva ou situação de viagem."
    )
