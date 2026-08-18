"""
Base de conhecimento multilíngue para o módulo RAG.

v2.0: Expande a base de documentos com versões em inglês e espanhol,
além de novos documentos sobre regulamentações internacionais.
"""

from src.rag.documentos import DOCUMENTOS_POLITICAS

# Documentos adicionais em inglês
DOCUMENTOS_EN: list[dict] = [
    {
        "id": "en_001",
        "titulo": "Passenger Rights - EU Regulation 261/2004",
        "conteudo": (
            "Under EU Regulation 261/2004, passengers flying from EU airports "
            "or with EU carriers are entitled to compensation for cancellations "
            "and long delays. For flights up to 1500km, compensation is EUR 250. "
            "For flights between 1500-3500km, EUR 400. For flights over 3500km, "
            "EUR 600. The airline must offer re-routing or refund within 7 days. "
            "Right to care includes meals, refreshments, hotel accommodation, "
            "and transport between hotel and airport."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "EU regulation", "261/2004", "compensation", "cancellation",
            "delay", "refund", "re-routing", "passenger rights"
        ],
        "idioma": "en",
    },
    {
        "id": "en_002",
        "titulo": "US DOT Passenger Protection Rules",
        "conteudo": (
            "Under US Department of Transportation rules, airlines must refund "
            "tickets for cancelled or significantly changed flights. Tarmac delays "
            "exceeding 3 hours on domestic flights require deplaning opportunity. "
            "Airlines must compensate involuntarily bumped passengers: 200% of "
            "one-way fare for 1-2 hour delays (domestic), 400% for longer delays, "
            "up to $1,550 maximum. Baggage liability limited to $3,800 for domestic."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "DOT", "US rules", "refund", "tarmac delay", "bumped",
            "compensation", "baggage", "passenger protection"
        ],
        "idioma": "en",
    },
    {
        "id": "en_003",
        "titulo": "Montreal Convention - International Air Transport",
        "conteudo": (
            "The Montreal Convention 1999 establishes airline liability limits "
            "for international flights. Baggage liability: up to 1,288 SDR "
            "(Special Drawing Rights) per passenger. Delay liability: up to "
            "5,346 SDR per passenger. Death/injury liability: up to 128,821 SDR "
            "(strict liability) with unlimited liability above if negligence proven. "
            "Claims must be filed within 2 years. Written complaint for baggage "
            "damage within 7 days, delay within 21 days of receipt."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "Montreal Convention", "international", "liability", "SDR",
            "baggage", "delay", "claim", "deadline"
        ],
        "idioma": "en",
    },
]

# Documentos adicionais em espanhol
DOCUMENTOS_ES: list[dict] = [
    {
        "id": "es_001",
        "titulo": "Derechos del Pasajero - Regulación Mercosur",
        "conteudo": (
            "En vuelos dentro del Mercosur, los pasajeros tienen derecho a "
            "asistencia material según el tiempo de espera. A partir de 1 hora: "
            "comunicación. A partir de 2 horas: alimentación. A partir de 4 horas: "
            "alojamiento y transporte. En caso de cancelación, el pasajero puede "
            "elegir entre reembolso total, reubicación en el próximo vuelo "
            "disponible o transporte alternativo. La aerolínea debe informar "
            "inmediatamente sobre cambios en el estado del vuelo."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "Mercosur", "derechos", "pasajero", "cancelación",
            "reembolso", "asistencia", "reubicación"
        ],
        "idioma": "es",
    },
    {
        "id": "es_002",
        "titulo": "Regulación Aeronáutica Argentina - ANAC Res. 1532/98",
        "conteudo": (
            "La Administración Nacional de Aviación Civil de Argentina establece "
            "que en caso de demora superior a 4 horas o cancelación, el pasajero "
            "tiene derecho a comunicación gratuita, refrigerios, comidas y "
            "alojamiento según corresponda. La compensación por denegación de "
            "embarque involuntaria es obligatoria. Los reclamos deben presentarse "
            "dentro de los 30 días del hecho. El transportador debe ofrecer "
            "alternativas de vuelo sin costo adicional."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "Argentina", "ANAC", "demora", "cancelación",
            "compensación", "denegación embarque", "reclamo"
        ],
        "idioma": "es",
    },
]

# Documentos adicionais em português (expandindo a base v1.0)
DOCUMENTOS_ADICIONAIS_PT: list[dict] = [
    {
        "id": "pol_011",
        "titulo": "Convenção de Montreal - Voos Internacionais",
        "conteudo": (
            "A Convenção de Montreal de 1999 estabelece limites de "
            "responsabilidade das companhias aéreas para voos internacionais. "
            "Limite para bagagem: até 1.288 DES por passageiro. Limite para "
            "atraso: até 5.346 DES por passageiro. O prazo para reclamação "
            "de dano à bagagem é de 7 dias. Para atraso na entrega da bagagem, "
            "21 dias após o recebimento. Ações judiciais devem ser propostas "
            "em até 2 anos. O Brasil é signatário da Convenção desde 2006."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "Convenção de Montreal", "internacional", "DES",
            "responsabilidade", "bagagem", "atraso", "prazo"
        ],
        "idioma": "pt",
    },
    {
        "id": "pol_012",
        "titulo": "PROCON e Juizado Especial - Reclamações de Viagem",
        "conteudo": (
            "O passageiro pode registrar reclamação no PROCON do seu estado "
            "ou na plataforma consumidor.gov.br contra a companhia aérea. "
            "Para valores até 20 salários mínimos, pode acionar o Juizado "
            "Especial Cível sem advogado. Documentação necessária: bilhete "
            "de embarque, comprovante de pagamento, registros de comunicação "
            "com a empresa, fotos/vídeos da situação e recibos de gastos extras. "
            "O prazo prescricional para ações de danos morais e materiais "
            "é de 5 anos (CDC) ou 2 anos (Convenção de Montreal para voos "
            "internacionais)."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "PROCON", "Juizado Especial", "reclamação", "consumidor",
            "documentação", "prazo", "ação judicial", "CDC"
        ],
        "idioma": "pt",
    },
    {
        "id": "pol_013",
        "titulo": "Seguro Viagem e Cobertura de Cancelamento",
        "conteudo": (
            "O seguro viagem pode cobrir despesas adicionais em caso de "
            "cancelamento ou atraso de voo, incluindo: hospedagem extra, "
            "alimentação, transporte alternativo, e comunicação. A cobertura "
            "varia conforme o plano contratado. É importante verificar se o "
            "seguro cobre 'interrupção de viagem' e 'atraso de voo'. Cartões "
            "de crédito premium (Platinum, Black, Infinite) geralmente oferecem "
            "seguro viagem incluído. O prazo para acionar o seguro é "
            "geralmente de 24 a 72 horas após o evento."
        ),
        "categoria": "assistencia",
        "palavras_chave": [
            "seguro viagem", "cobertura", "cancelamento", "cartão de crédito",
            "hospedagem", "interrupção", "sinistro"
        ],
        "idioma": "pt",
    },
    {
        "id": "pol_014",
        "titulo": "Conexões e Escalas - Responsabilidade da Companhia",
        "conteudo": (
            "Quando voos com conexão são vendidos no mesmo bilhete, a companhia "
            "é responsável por garantir a continuidade da viagem. Se o passageiro "
            "perde a conexão por atraso/cancelamento do primeiro trecho, tem "
            "direito a reacomodação sem custo no próximo voo disponível. "
            "A assistência material é devida durante todo o período de espera. "
            "Se as conexões foram compradas em bilhetes separados, a "
            "responsabilidade pode ser limitada ao trecho afetado."
        ),
        "categoria": "reacomodacao",
        "palavras_chave": [
            "conexão", "escala", "bilhete", "reacomodação",
            "continuidade", "perda conexão", "responsabilidade"
        ],
        "idioma": "pt",
    },
]


def detectar_idioma(texto: str) -> str:
    """Detecta o idioma principal do texto (simplificado).

    Args:
        texto: Texto para detecção de idioma.

    Returns:
        Código do idioma: 'pt', 'en', ou 'es'.
    """
    texto_lower = texto.lower()

    # Indicadores de inglês
    palavras_en = [
        "flight", "cancelled", "delay", "airport", "boarding",
        "refund", "compensation", "rights", "baggage", "my",
        "the", "is", "was", "have", "need", "help",
    ]

    # Indicadores de espanhol
    palavras_es = [
        "vuelo", "cancelado", "demora", "aeropuerto", "embarque",
        "reembolso", "compensación", "derechos", "equipaje",
        "necesito", "ayuda", "está", "fue", "tengo",
    ]

    # Indicadores de português
    palavras_pt = [
        "voo", "cancelado", "atraso", "aeroporto", "embarque",
        "reembolso", "compensação", "direitos", "bagagem",
        "preciso", "ajuda", "está", "foi", "tenho", "meu", "minha",
    ]

    score_en = sum(1 for p in palavras_en if p in texto_lower)
    score_es = sum(1 for p in palavras_es if p in texto_lower)
    score_pt = sum(1 for p in palavras_pt if p in texto_lower)

    if score_en > score_es and score_en > score_pt:
        return "en"
    elif score_es > score_pt:
        return "es"
    return "pt"


def obter_documentos(idioma: Optional[str] = None,
                     incluir_internacionais: bool = True) -> list[dict]:
    """Retorna documentos filtrados por idioma.

    Args:
        idioma: Filtrar por idioma ('pt', 'en', 'es'). None retorna todos.
        incluir_internacionais: Se True, inclui documentos internacionais
                                independente do idioma selecionado.

    Returns:
        Lista de documentos para indexação pelo RAG.
    """
    # Base original (português)
    todos = list(DOCUMENTOS_POLITICAS)

    # Adicionar documentos expandidos em PT
    todos.extend(DOCUMENTOS_ADICIONAIS_PT)

    # Adicionar documentos multilíngues
    if idioma is None or incluir_internacionais:
        todos.extend(DOCUMENTOS_EN)
        todos.extend(DOCUMENTOS_ES)
    elif idioma == "en":
        todos.extend(DOCUMENTOS_EN)
    elif idioma == "es":
        todos.extend(DOCUMENTOS_ES)

    # Garantir campo idioma em todos os documentos
    for doc in todos:
        if "idioma" not in doc:
            doc["idioma"] = "pt"

    return todos


# Alias conveniente
def obter_todos_documentos() -> list[dict]:
    """Retorna todos os documentos disponíveis (todos os idiomas)."""
    return obter_documentos(idioma=None, incluir_internacionais=True)
