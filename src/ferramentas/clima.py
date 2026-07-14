"""
Ferramenta de consulta climática para aeroportos brasileiros.
Utiliza a API gratuita Open-Meteo para obter condições atuais e previsão 24h.
"""

import requests
from langchain_core.tools import tool


# Lookup de coordenadas (latitude, longitude) para aeroportos brasileiros
COORDENADAS: dict[str, tuple[float, float]] = {
    "GRU": (-23.43, -46.47),   # São Paulo - Guarulhos
    "GIG": (-22.81, -43.25),   # Rio de Janeiro - Galeão
    "BSB": (-15.87, -47.92),   # Brasília
    "SSA": (-12.91, -38.33),   # Salvador
    "CNF": (-19.63, -43.97),   # Belo Horizonte - Confins
    "CWB": (-25.43, -49.27),   # Curitiba
    "POA": (-29.99, -51.17),   # Porto Alegre
    "REC": (-8.13, -34.91),    # Recife
}


# Mapeamento de weather_code para condições legíveis em português
def _mapear_condicao(weather_code: int) -> str:
    """Mapeia weather_code da Open-Meteo para descrição em português."""
    if weather_code == 0:
        return "Céu limpo"
    elif 1 <= weather_code <= 3:
        return "Parcialmente nublado"
    elif weather_code in (45, 48):
        return "Neblina"
    elif 51 <= weather_code <= 55:
        return "Garoa"
    elif 61 <= weather_code <= 65:
        return "Chuva"
    elif 71 <= weather_code <= 77:
        return "Neve"
    elif 80 <= weather_code <= 82:
        return "Pancadas de chuva"
    elif 95 <= weather_code <= 99:
        return "Tempestade"
    else:
        return "Condição desconhecida"


def _detectar_condicoes_adversas(
    weather_code: int, visibility: float, wind_speed: float
) -> list[str]:
    """
    Detecta condições climáticas adversas com base nos critérios:
    - Tempestade: weather_code 95-99
    - Neve: weather_code 71-77
    - Neblina com visibilidade < 1000m: weather_code 45/48 e visibility < 1000
    - Ventos fortes: wind_speed > 60 km/h
    - Chuva intensa: weather_code 65 ou 82
    """
    alertas = []

    if 95 <= weather_code <= 99:
        alertas.append("Tempestade ativa na região")
    if 71 <= weather_code <= 77:
        alertas.append("Neve na região")
    if weather_code in (45, 48) and visibility < 1000:
        alertas.append(f"Neblina densa (visibilidade: {visibility:.0f}m)")
    if wind_speed > 60:
        alertas.append(f"Ventos fortes ({wind_speed:.1f} km/h)")
    if weather_code in (65, 82):
        alertas.append("Chuva intensa")

    return alertas


def _formatar_clima(current: dict, codigo_aeroporto: str) -> str:
    """Formata os dados climáticos em string legível."""
    temperatura = current.get("temperature_2m", "N/A")
    weather_code = current.get("weather_code", -1)
    wind_speed = current.get("wind_speed_10m", 0)
    visibility = current.get("visibility", 10000)

    condicao = _mapear_condicao(weather_code)
    alertas = _detectar_condicoes_adversas(weather_code, visibility, wind_speed)

    linhas = [
        f"Clima em {codigo_aeroporto}:",
        f"  Temperatura: {temperatura}°C",
        f"  Condição: {condicao}",
        f"  Vento: {wind_speed} km/h",
        f"  Visibilidade: {visibility:.0f}m",
    ]

    if alertas:
        linhas.append("  ⚠️ CONDIÇÕES ADVERSAS DETECTADAS:")
        for alerta in alertas:
            linhas.append(f"    - {alerta}")
    else:
        linhas.append("  ✅ Sem condições adversas detectadas")

    return "\n".join(linhas)


@tool
def consultar_clima(codigo_aeroporto: str) -> str:
    """
    Consulta condições climáticas atuais e previsão 24h para um aeroporto.
    Usa API gratuita Open-Meteo. Retorna: temperatura, condição, vento,
    visibilidade e alertas de condições adversas.
    """
    coords = COORDENADAS.get(codigo_aeroporto.upper())
    if not coords:
        return f"Aeroporto '{codigo_aeroporto}' não encontrado na base de dados."

    lat, lon = coords
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weather_code,wind_speed_10m,visibility"
        f"&hourly=temperature_2m,weather_code"
        f"&forecast_days=1&timezone=America/Sao_Paulo"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data["current"]
        return _formatar_clima(current, codigo_aeroporto.upper())
    except requests.exceptions.Timeout:
        return (
            f"Erro ao consultar clima para {codigo_aeroporto}: "
            "timeout na conexão (limite de 10s excedido)."
        )
    except requests.exceptions.ConnectionError:
        return (
            f"Erro ao consultar clima para {codigo_aeroporto}: "
            "falha na conexão com o serviço meteorológico."
        )
    except Exception as e:
        return f"Erro ao consultar clima para {codigo_aeroporto}: {str(e)}"
