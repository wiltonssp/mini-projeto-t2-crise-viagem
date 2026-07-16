"""
Ferramenta de consulta de status de voo.

Base de dados simulada com voos em diferentes status para fins acadêmicos.
Utiliza o decorador @tool do langchain_core.tools para integração com LangGraph.
"""

from datetime import date

from langchain_core.tools import tool


def _hoje() -> str:
    """Retorna a data de hoje no formato YYYY-MM-DD."""
    return date.today().isoformat()


def _gerar_voos_db() -> dict[str, dict]:
    """Gera a base de dados de voos com horários sempre no dia atual."""
    hoje = _hoje()
    return {
        "ABC123": {
            "numero_voo": "LA3456",
            "origem": "GRU",
            "destino": "GIG",
            "horario_partida": f"{hoje}T14:30:00",
            "horario_chegada": f"{hoje}T15:45:00",
            "status": "cancelado",
            "motivo": "Condições meteorológicas adversas (mau tempo)",
        },
        "DEF456": {
            "numero_voo": "G3 1020",
            "origem": "BSB",
            "destino": "SSA",
            "horario_partida": f"{hoje}T10:00:00",
            "horario_chegada": f"{hoje}T12:30:00",
            "status": "atrasado",
            "motivo": "Manutenção não programada da aeronave (atraso estimado de 2h)",
        },
        "GHI789": {
            "numero_voo": "AD4512",
            "origem": "CNF",
            "destino": "GRU",
            "horario_partida": f"{hoje}T08:15:00",
            "horario_chegada": f"{hoje}T09:30:00",
            "status": "confirmado",
            "motivo": "N/A",
        },
        "JKL012": {
            "numero_voo": "LA1234",
            "origem": "GIG",
            "destino": "BSB",
            "horario_partida": f"{hoje}T16:00:00",
            "horario_chegada": f"{hoje}T17:45:00",
            "status": "embarcando",
            "motivo": "N/A",
        },
        "MNO345": {
            "numero_voo": "G3 2078",
            "origem": "CWB",
            "destino": "POA",
            "horario_partida": f"{hoje}T07:00:00",
            "horario_chegada": f"{hoje}T08:20:00",
            "status": "cancelado",
            "motivo": "Neblina intensa no aeroporto de destino",
        },
        "XYZ789": {
            "numero_voo": "LA5678",
            "origem": "GRU",
            "destino": "GIG",
            "horario_partida": f"{hoje}T11:00:00",
            "horario_chegada": f"{hoje}T14:30:00",
            "status": "atrasado",
            "motivo": "Conexão perdida em BSB devido a atraso do voo anterior",
        },
    }


# Base de dados simulada de voos (gerada dinamicamente com a data atual)
VOOS_DB: dict[str, dict] = _gerar_voos_db()


@tool
def consultar_status_voo(codigo_reserva: str) -> str:
    """Consulta o status de um voo pelo código de reserva.

    Retorna informações completas do voo incluindo número, origem, destino,
    horários de partida e chegada, status atual e motivo de alteração.

    Args:
        codigo_reserva: Código alfanumérico de 6 caracteres da reserva (ex: ABC123).

    Returns:
        String formatada com os dados do voo ou mensagem de erro se não encontrado.
    """
    voo = VOOS_DB.get(codigo_reserva)

    if not voo:
        return (
            f"Reserva '{codigo_reserva}' não encontrada no sistema. "
            "Verifique se o código está correto e tente novamente."
        )

    return (
        f"Voo: {voo['numero_voo']}\n"
        f"Origem: {voo['origem']}\n"
        f"Destino: {voo['destino']}\n"
        f"Partida: {voo['horario_partida']}\n"
        f"Chegada: {voo['horario_chegada']}\n"
        f"Status: {voo['status']}\n"
        f"Motivo: {voo['motivo']}"
    )
