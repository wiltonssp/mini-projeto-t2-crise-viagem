"""
Ferramenta de consulta de transporte alternativo.

Busca opções de transporte (voo, ônibus, trem) entre aeroportos/cidades
brasileiras usando uma base simulada com rotas realistas.
"""

from langchain_core.tools import tool


# Base simulada de rotas alternativas entre aeroportos/cidades brasileiras.
# Chaves: tuplas (origem, destino) com códigos IATA.
# Valores: lista de opções com tipo, origem, destino, partida, duração e conexões.
ROTAS_DB: dict[tuple[str, str], list[dict]] = {
    ("GRU", "GIG"): [
        {"tipo": "voo", "origem": "GRU", "destino": "GIG",
         "partida": "18:00", "duracao": "1h15min", "conexoes": 0},
        {"tipo": "onibus", "origem": "GRU", "destino": "GIG",
         "partida": "16:30", "duracao": "6h00min", "conexoes": 0},
        {"tipo": "trem", "origem": "GRU", "destino": "GIG",
         "partida": "20:00", "duracao": "5h30min", "conexoes": 1},
    ],
    ("GRU", "BSB"): [
        {"tipo": "voo", "origem": "GRU", "destino": "BSB",
         "partida": "07:30", "duracao": "1h45min", "conexoes": 0},
        {"tipo": "onibus", "origem": "GRU", "destino": "BSB",
         "partida": "22:00", "duracao": "14h00min", "conexoes": 0},
    ],
    ("GIG", "SSA"): [
        {"tipo": "voo", "origem": "GIG", "destino": "SSA",
         "partida": "09:15", "duracao": "2h20min", "conexoes": 0},
        {"tipo": "onibus", "origem": "GIG", "destino": "SSA",
         "partida": "18:00", "duracao": "24h00min", "conexoes": 1},
    ],
    ("BSB", "SSA"): [
        {"tipo": "voo", "origem": "BSB", "destino": "SSA",
         "partida": "10:00", "duracao": "2h00min", "conexoes": 0},
        {"tipo": "onibus", "origem": "BSB", "destino": "SSA",
         "partida": "19:00", "duracao": "20h00min", "conexoes": 1},
    ],
    ("GRU", "CWB"): [
        {"tipo": "voo", "origem": "GRU", "destino": "CWB",
         "partida": "08:00", "duracao": "1h10min", "conexoes": 0},
        {"tipo": "onibus", "origem": "GRU", "destino": "CWB",
         "partida": "23:00", "duracao": "6h00min", "conexoes": 0},
        {"tipo": "trem", "origem": "GRU", "destino": "CWB",
         "partida": "06:30", "duracao": "4h30min", "conexoes": 0},
    ],
    ("CWB", "POA"): [
        {"tipo": "voo", "origem": "CWB", "destino": "POA",
         "partida": "11:00", "duracao": "1h20min", "conexoes": 0},
        {"tipo": "onibus", "origem": "CWB", "destino": "POA",
         "partida": "21:00", "duracao": "10h00min", "conexoes": 0},
    ],
    ("GRU", "REC"): [
        {"tipo": "voo", "origem": "GRU", "destino": "REC",
         "partida": "06:00", "duracao": "3h30min", "conexoes": 0},
        {"tipo": "onibus", "origem": "GRU", "destino": "REC",
         "partida": "14:00", "duracao": "36h00min", "conexoes": 2},
    ],
    ("GIG", "BSB"): [
        {"tipo": "voo", "origem": "GIG", "destino": "BSB",
         "partida": "12:30", "duracao": "1h50min", "conexoes": 0},
        {"tipo": "onibus", "origem": "GIG", "destino": "BSB",
         "partida": "20:00", "duracao": "16h00min", "conexoes": 0},
    ],
}


def _duracao_para_minutos(duracao: str) -> int:
    """Converte string de duração (ex: '1h15min') para minutos totais."""
    horas = 0
    minutos = 0
    try:
        if "h" in duracao:
            partes = duracao.split("h")
            horas = int(partes[0])
            resto = partes[1].replace("min", "").strip()
            if resto:
                minutos = int(resto)
        elif "min" in duracao:
            minutos = int(duracao.replace("min", "").strip())
    except (ValueError, IndexError):
        return 9999  # Valor alto para ordenar ao final em caso de erro
    return horas * 60 + minutos


@tool
def consultar_transporte_alternativo(origem: str, destino: str) -> str:
    """
    Busca opções de transporte alternativo entre origem e destino.
    Retorna opções ordenadas por tempo de viagem (voos, ônibus, trens).
    Parâmetros:
        origem: código IATA do aeroporto de origem (ex: GRU, GIG, BSB)
        destino: código IATA do aeroporto de destino (ex: GIG, SSA, CWB)
    """
    origem_upper = origem.strip().upper()
    destino_upper = destino.strip().upper()

    rotas = ROTAS_DB.get((origem_upper, destino_upper), [])

    if not rotas:
        return (
            f"Nenhuma opção de transporte alternativo encontrada "
            f"entre {origem_upper} e {destino_upper}."
        )

    # Ordenar por duração estimada (convertendo para minutos para ordenação correta)
    rotas_ordenadas = sorted(rotas, key=lambda r: _duracao_para_minutos(r["duracao"]))

    # Limitar a no máximo 10 opções
    rotas_ordenadas = rotas_ordenadas[:10]

    linhas = [f"Opções de transporte {origem_upper} → {destino_upper}:"]
    for i, r in enumerate(rotas_ordenadas, 1):
        linhas.append(
            f"  {i}. [{r['tipo'].upper()}] "
            f"Origem: {r['origem']} | Destino: {r['destino']} | "
            f"Partida: {r['partida']} | "
            f"Duração: {r['duracao']} | Conexões: {r['conexoes']}"
        )

    return "\n".join(linhas)
