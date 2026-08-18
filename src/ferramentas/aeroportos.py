"""
Base de dados expandida de aeroportos internacionais (IATA).

v3.0: Cobertura internacional com coordenadas para consulta climática,
fusos horários e informações de contato.
"""

from typing import Optional


# Base expandida de aeroportos com cobertura internacional
# Formato: código IATA → dict com informações do aeroporto
AEROPORTOS_DB: dict[str, dict] = {
    # ===== BRASIL =====
    "GRU": {
        "nome": "Aeroporto Internacional de São Paulo-Guarulhos",
        "cidade": "São Paulo",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -23.43,
        "longitude": -46.47,
        "fuso": "America/Sao_Paulo",
        "contato": "+55 11 2445-2945",
    },
    "GIG": {
        "nome": "Aeroporto Internacional do Rio de Janeiro-Galeão",
        "cidade": "Rio de Janeiro",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -22.81,
        "longitude": -43.25,
        "fuso": "America/Sao_Paulo",
        "contato": "+55 21 3004-6050",
    },
    "BSB": {
        "nome": "Aeroporto Internacional de Brasília",
        "cidade": "Brasília",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -15.87,
        "longitude": -47.92,
        "fuso": "America/Sao_Paulo",
        "contato": "+55 61 3364-9000",
    },
    "SSA": {
        "nome": "Aeroporto Internacional de Salvador",
        "cidade": "Salvador",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -12.91,
        "longitude": -38.33,
        "fuso": "America/Bahia",
        "contato": "+55 71 3204-1010",
    },
    "CNF": {
        "nome": "Aeroporto Internacional de Confins",
        "cidade": "Belo Horizonte",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -19.63,
        "longitude": -43.97,
        "fuso": "America/Sao_Paulo",
        "contato": "+55 31 3689-2700",
    },
    "CWB": {
        "nome": "Aeroporto Internacional de Curitiba",
        "cidade": "Curitiba",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -25.43,
        "longitude": -49.27,
        "fuso": "America/Sao_Paulo",
        "contato": "+55 41 3381-1515",
    },
    "POA": {
        "nome": "Aeroporto Internacional Salgado Filho",
        "cidade": "Porto Alegre",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -29.99,
        "longitude": -51.17,
        "fuso": "America/Sao_Paulo",
        "contato": "+55 51 3358-2000",
    },
    "REC": {
        "nome": "Aeroporto Internacional do Recife",
        "cidade": "Recife",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -8.13,
        "longitude": -34.91,
        "fuso": "America/Recife",
        "contato": "+55 81 3322-4188",
    },
    "FOR": {
        "nome": "Aeroporto Internacional de Fortaleza",
        "cidade": "Fortaleza",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -3.78,
        "longitude": -38.53,
        "fuso": "America/Fortaleza",
        "contato": "+55 85 3392-1030",
    },
    "MAO": {
        "nome": "Aeroporto Internacional Eduardo Gomes",
        "cidade": "Manaus",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -3.04,
        "longitude": -60.05,
        "fuso": "America/Manaus",
        "contato": "+55 92 3652-1210",
    },
    "FLN": {
        "nome": "Aeroporto Internacional de Florianópolis",
        "cidade": "Florianópolis",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -27.67,
        "longitude": -48.55,
        "fuso": "America/Sao_Paulo",
        "contato": "+55 48 3331-4000",
    },
    "VCP": {
        "nome": "Aeroporto Internacional de Viracopos",
        "cidade": "Campinas",
        "pais": "Brasil",
        "codigo_pais": "BR",
        "latitude": -23.01,
        "longitude": -47.13,
        "fuso": "America/Sao_Paulo",
        "contato": "+55 19 3725-5000",
    },
    # ===== AMÉRICA DO SUL =====
    "EZE": {
        "nome": "Aeropuerto Internacional Ministro Pistarini",
        "cidade": "Buenos Aires",
        "pais": "Argentina",
        "codigo_pais": "AR",
        "latitude": -34.82,
        "longitude": -58.54,
        "fuso": "America/Argentina/Buenos_Aires",
        "contato": "+54 11 5480-6111",
    },
    "SCL": {
        "nome": "Aeropuerto Internacional Arturo Merino Benítez",
        "cidade": "Santiago",
        "pais": "Chile",
        "codigo_pais": "CL",
        "latitude": -33.39,
        "longitude": -70.79,
        "fuso": "America/Santiago",
        "contato": "+56 2 2690-1752",
    },
    "BOG": {
        "nome": "Aeropuerto Internacional El Dorado",
        "cidade": "Bogotá",
        "pais": "Colômbia",
        "codigo_pais": "CO",
        "latitude": 4.70,
        "longitude": -74.15,
        "fuso": "America/Bogota",
        "contato": "+57 1 266-2000",
    },
    "LIM": {
        "nome": "Aeropuerto Internacional Jorge Chávez",
        "cidade": "Lima",
        "pais": "Peru",
        "codigo_pais": "PE",
        "latitude": -12.02,
        "longitude": -77.11,
        "fuso": "America/Lima",
        "contato": "+51 1 517-3100",
    },
    "MVD": {
        "nome": "Aeropuerto Internacional de Carrasco",
        "cidade": "Montevidéu",
        "pais": "Uruguai",
        "codigo_pais": "UY",
        "latitude": -34.84,
        "longitude": -56.03,
        "fuso": "America/Montevideo",
        "contato": "+598 2604-0386",
    },
    # ===== AMÉRICA DO NORTE =====
    "JFK": {
        "nome": "John F. Kennedy International Airport",
        "cidade": "Nova York",
        "pais": "Estados Unidos",
        "codigo_pais": "US",
        "latitude": 40.64,
        "longitude": -73.78,
        "fuso": "America/New_York",
        "contato": "+1 718-244-4444",
    },
    "MIA": {
        "nome": "Miami International Airport",
        "cidade": "Miami",
        "pais": "Estados Unidos",
        "codigo_pais": "US",
        "latitude": 25.79,
        "longitude": -80.29,
        "fuso": "America/New_York",
        "contato": "+1 305-876-7000",
    },
    "LAX": {
        "nome": "Los Angeles International Airport",
        "cidade": "Los Angeles",
        "pais": "Estados Unidos",
        "codigo_pais": "US",
        "latitude": 33.94,
        "longitude": -118.41,
        "fuso": "America/Los_Angeles",
        "contato": "+1 310-646-5252",
    },
    "ORD": {
        "nome": "O'Hare International Airport",
        "cidade": "Chicago",
        "pais": "Estados Unidos",
        "codigo_pais": "US",
        "latitude": 41.97,
        "longitude": -87.91,
        "fuso": "America/Chicago",
        "contato": "+1 773-686-2200",
    },
    "MEX": {
        "nome": "Aeropuerto Internacional Benito Juárez",
        "cidade": "Cidade do México",
        "pais": "México",
        "codigo_pais": "MX",
        "latitude": 19.44,
        "longitude": -99.07,
        "fuso": "America/Mexico_City",
        "contato": "+52 55 2482-2400",
    },
    "YYZ": {
        "nome": "Toronto Pearson International Airport",
        "cidade": "Toronto",
        "pais": "Canadá",
        "codigo_pais": "CA",
        "latitude": 43.68,
        "longitude": -79.63,
        "fuso": "America/Toronto",
        "contato": "+1 416-247-7678",
    },
    # ===== EUROPA =====
    "LHR": {
        "nome": "London Heathrow Airport",
        "cidade": "Londres",
        "pais": "Reino Unido",
        "codigo_pais": "GB",
        "latitude": 51.47,
        "longitude": -0.46,
        "fuso": "Europe/London",
        "contato": "+44 844-335-1801",
    },
    "CDG": {
        "nome": "Aéroport Charles de Gaulle",
        "cidade": "Paris",
        "pais": "França",
        "codigo_pais": "FR",
        "latitude": 49.01,
        "longitude": 2.55,
        "fuso": "Europe/Paris",
        "contato": "+33 1 7036-3950",
    },
    "FRA": {
        "nome": "Frankfurt Airport",
        "cidade": "Frankfurt",
        "pais": "Alemanha",
        "codigo_pais": "DE",
        "latitude": 50.03,
        "longitude": 8.57,
        "fuso": "Europe/Berlin",
        "contato": "+49 69 6900",
    },
    "MAD": {
        "nome": "Aeropuerto Adolfo Suárez Madrid-Barajas",
        "cidade": "Madrid",
        "pais": "Espanha",
        "codigo_pais": "ES",
        "latitude": 40.49,
        "longitude": -3.57,
        "fuso": "Europe/Madrid",
        "contato": "+34 91 321-1000",
    },
    "FCO": {
        "nome": "Aeroporto Leonardo da Vinci-Fiumicino",
        "cidade": "Roma",
        "pais": "Itália",
        "codigo_pais": "IT",
        "latitude": 41.80,
        "longitude": 12.25,
        "fuso": "Europe/Rome",
        "contato": "+39 06 65951",
    },
    "LIS": {
        "nome": "Aeroporto Humberto Delgado",
        "cidade": "Lisboa",
        "pais": "Portugal",
        "codigo_pais": "PT",
        "latitude": 38.77,
        "longitude": -9.13,
        "fuso": "Europe/Lisbon",
        "contato": "+351 21 841-3500",
    },
    "AMS": {
        "nome": "Amsterdam Airport Schiphol",
        "cidade": "Amsterdã",
        "pais": "Holanda",
        "codigo_pais": "NL",
        "latitude": 52.31,
        "longitude": 4.77,
        "fuso": "Europe/Amsterdam",
        "contato": "+31 20 794-0800",
    },
    # ===== ÁSIA / OCEANIA =====
    "DXB": {
        "nome": "Dubai International Airport",
        "cidade": "Dubai",
        "pais": "Emirados Árabes",
        "codigo_pais": "AE",
        "latitude": 25.25,
        "longitude": 55.36,
        "fuso": "Asia/Dubai",
        "contato": "+971 4 224-5555",
    },
    "NRT": {
        "nome": "Narita International Airport",
        "cidade": "Tóquio",
        "pais": "Japão",
        "codigo_pais": "JP",
        "latitude": 35.76,
        "longitude": 140.39,
        "fuso": "Asia/Tokyo",
        "contato": "+81 476-34-8000",
    },
    "SIN": {
        "nome": "Singapore Changi Airport",
        "cidade": "Singapura",
        "pais": "Singapura",
        "codigo_pais": "SG",
        "latitude": 1.36,
        "longitude": 103.99,
        "fuso": "Asia/Singapore",
        "contato": "+65 6595-6868",
    },
    "SYD": {
        "nome": "Sydney Kingsford Smith Airport",
        "cidade": "Sydney",
        "pais": "Austrália",
        "codigo_pais": "AU",
        "latitude": -33.95,
        "longitude": 151.18,
        "fuso": "Australia/Sydney",
        "contato": "+61 2 9667-9111",
    },
    # ===== ÁFRICA =====
    "JNB": {
        "nome": "O. R. Tambo International Airport",
        "cidade": "Joanesburgo",
        "pais": "África do Sul",
        "codigo_pais": "ZA",
        "latitude": -26.14,
        "longitude": 28.25,
        "fuso": "Africa/Johannesburg",
        "contato": "+27 11 921-6262",
    },
}


def obter_aeroporto(codigo_iata: str) -> Optional[dict]:
    """Obtém informações de um aeroporto pelo código IATA.

    Args:
        codigo_iata: Código IATA de 3 letras (ex: GRU, JFK).

    Returns:
        Dict com informações do aeroporto ou None se não encontrado.
    """
    return AEROPORTOS_DB.get(codigo_iata.upper())


def obter_coordenadas(codigo_iata: str) -> Optional[tuple[float, float]]:
    """Obtém coordenadas (lat, lon) de um aeroporto.

    Args:
        codigo_iata: Código IATA.

    Returns:
        Tupla (latitude, longitude) ou None.
    """
    aero = AEROPORTOS_DB.get(codigo_iata.upper())
    if aero:
        return (aero["latitude"], aero["longitude"])
    return None


def buscar_por_cidade(cidade: str) -> list[dict]:
    """Busca aeroportos por nome de cidade.

    Args:
        cidade: Nome da cidade (busca case-insensitive parcial).

    Returns:
        Lista de aeroportos encontrados.
    """
    cidade_lower = cidade.lower()
    resultados = []
    for codigo, info in AEROPORTOS_DB.items():
        if cidade_lower in info["cidade"].lower():
            resultados.append({"codigo": codigo, **info})
    return resultados


def buscar_por_pais(codigo_pais: str) -> list[dict]:
    """Busca aeroportos por código de país (ISO 2 letras).

    Args:
        codigo_pais: Código ISO do país (ex: BR, US, PT).

    Returns:
        Lista de aeroportos do país.
    """
    codigo = codigo_pais.upper()
    resultados = []
    for cod_iata, info in AEROPORTOS_DB.items():
        if info["codigo_pais"] == codigo:
            resultados.append({"codigo": cod_iata, **info})
    return resultados


def listar_todos() -> list[dict]:
    """Lista todos os aeroportos disponíveis.

    Returns:
        Lista com código e informações de cada aeroporto.
    """
    return [{"codigo": cod, **info} for cod, info in AEROPORTOS_DB.items()]


def total_aeroportos() -> int:
    """Retorna o número total de aeroportos na base."""
    return len(AEROPORTOS_DB)


# Mapeamento de cidades comuns para códigos IATA (multilíngue)
MAPA_CIDADES: dict[str, str] = {
    # Português
    "são paulo": "GRU", "sao paulo": "GRU", "guarulhos": "GRU",
    "rio de janeiro": "GIG", "rio": "GIG", "galeão": "GIG", "galeao": "GIG",
    "brasília": "BSB", "brasilia": "BSB",
    "salvador": "SSA", "belo horizonte": "CNF", "confins": "CNF",
    "curitiba": "CWB", "porto alegre": "POA", "recife": "REC",
    "fortaleza": "FOR", "manaus": "MAO", "florianópolis": "FLN",
    "florianopolis": "FLN", "campinas": "VCP",
    # Espanhol
    "buenos aires": "EZE", "santiago": "SCL", "bogotá": "BOG",
    "bogota": "BOG", "lima": "LIM", "montevidéu": "MVD", "montevideo": "MVD",
    "cidade do méxico": "MEX", "ciudad de mexico": "MEX",
    # Inglês
    "new york": "JFK", "nova york": "JFK", "nova iorque": "JFK",
    "miami": "MIA", "los angeles": "LAX", "chicago": "ORD",
    "toronto": "YYZ", "london": "LHR", "londres": "LHR",
    "paris": "CDG", "frankfurt": "FRA", "madrid": "MAD",
    "roma": "FCO", "rome": "FCO", "lisboa": "LIS", "lisbon": "LIS",
    "amsterdam": "AMS", "amsterdã": "AMS",
    "dubai": "DXB", "tóquio": "NRT", "tokyo": "NRT", "toquio": "NRT",
    "singapura": "SIN", "singapore": "SIN",
    "sydney": "SYD", "joanesburgo": "JNB", "johannesburg": "JNB",
}


def resolver_cidade_para_iata(texto: str) -> Optional[str]:
    """Resolve nome de cidade para código IATA.

    Args:
        texto: Nome da cidade em qualquer idioma suportado.

    Returns:
        Código IATA ou None se não encontrado.
    """
    texto_lower = texto.lower().strip()

    # Busca direta no mapa
    if texto_lower in MAPA_CIDADES:
        return MAPA_CIDADES[texto_lower]

    # Busca parcial
    for cidade, codigo in MAPA_CIDADES.items():
        if cidade in texto_lower or texto_lower in cidade:
            return codigo

    # Tentar como código IATA direto
    if len(texto) == 3 and texto.upper() in AEROPORTOS_DB:
        return texto.upper()

    return None
