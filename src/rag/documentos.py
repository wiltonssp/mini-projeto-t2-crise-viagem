"""
Base de conhecimento para o módulo RAG.

Contém documentos sobre políticas da companhia aérea e legislação
de direitos do passageiro (Resolução ANAC 400/2016).
"""

DOCUMENTOS_POLITICAS: list[dict] = [
    {
        "id": "pol_001",
        "titulo": "Política de Reembolso - Cancelamento pela Companhia",
        "conteudo": (
            "Em caso de cancelamento de voo por iniciativa da companhia aérea, "
            "o passageiro tem direito ao reembolso integral do valor pago, "
            "incluindo tarifa e taxas aeroportuárias, no prazo de até 7 dias "
            "a partir da solicitação. O reembolso deve ser realizado pela mesma "
            "forma de pagamento utilizada na compra. Caso o bilhete tenha sido "
            "adquirido por meio de agência de viagens, o reembolso será feito "
            "pela agência conforme condições do contrato."
        ),
        "categoria": "reembolso",
        "palavras_chave": [
            "cancelamento", "reembolso", "devolução", "valor",
            "integral", "7 dias", "tarifa", "taxa"
        ],
    },
    {
        "id": "pol_002",
        "titulo": "Reacomodação de Passageiros",
        "conteudo": (
            "Quando um voo é cancelado ou sofre atraso superior a 4 horas, "
            "a companhia deve oferecer reacomodação gratuita no próximo voo "
            "disponível da própria empresa ou de outra companhia aérea que "
            "ofereça serviço equivalente para o mesmo destino. A reacomodação "
            "pode ser no próximo voo com lugar disponível ou em voo em horário "
            "conveniente para o passageiro, sem custo adicional. O passageiro "
            "não é obrigado a aceitar a reacomodação e pode optar pelo reembolso."
        ),
        "categoria": "reacomodacao",
        "palavras_chave": [
            "reacomodação", "próximo voo", "outra companhia",
            "voo disponível", "sem custo", "alternativa"
        ],
    },
    {
        "id": "pol_003",
        "titulo": "Assistência Material - Resolução ANAC 400/2016",
        "conteudo": (
            "Conforme a Resolução ANAC 400/2016, em caso de atraso, "
            "cancelamento ou preterição de embarque, a companhia aérea deve "
            "fornecer assistência material gratuita ao passageiro de acordo com "
            "o tempo de espera. A partir de 1 hora de atraso: facilidades de "
            "comunicação (internet, telefone). A partir de 2 horas: alimentação "
            "adequada (voucher, lanche, refeição). A partir de 4 horas: "
            "hospedagem (quando necessário pernoite) e transporte de ida e "
            "volta ao hotel. Passageiros que residem na localidade do aeroporto "
            "têm direito apenas ao transporte para casa e de volta ao aeroporto."
        ),
        "categoria": "assistencia",
        "palavras_chave": [
            "assistência material", "comunicação", "alimentação",
            "hospedagem", "1 hora", "2 horas", "4 horas",
            "ANAC 400", "transporte"
        ],
    },
    {
        "id": "pol_004",
        "titulo": "Compensação por Atraso de Voo",
        "conteudo": (
            "Em caso de atraso superior a 4 horas na chegada ao destino final, "
            "o passageiro pode solicitar compensação financeira à companhia aérea. "
            "A indenização por danos morais e materiais pode ser pleiteada "
            "judicialmente. O valor varia conforme jurisprudência, podendo "
            "alcançar entre R$ 3.000 e R$ 10.000 para voos domésticos. "
            "A companhia deve informar imediatamente o motivo do atraso e a "
            "nova previsão de horário de partida. O passageiro deve guardar "
            "comprovantes de gastos extras para eventual pedido de indenização "
            "por danos materiais."
        ),
        "categoria": "compensacao",
        "palavras_chave": [
            "atraso", "compensação", "indenização", "dano moral",
            "dano material", "4 horas", "valor", "judicial"
        ],
    },
    {
        "id": "pol_005",
        "titulo": "Direitos em Caso de Cancelamento - ANAC 400",
        "conteudo": (
            "Conforme a Resolução ANAC 400/2016, quando um voo é cancelado, "
            "o passageiro tem direito a escolher entre três opções: "
            "1) Reembolso integral, incluindo taxas, no prazo de 7 dias; "
            "2) Reacomodação no próximo voo disponível da mesma companhia ou "
            "de outra, para o mesmo destino; "
            "3) Execução do serviço por outra modalidade de transporte "
            "(terrestre, por exemplo). A companhia deve comunicar o "
            "cancelamento com antecedência mínima de 72 horas antes do horário "
            "de partida. Caso o aviso seja inferior a 72 horas, a assistência "
            "material é obrigatória independentemente do tempo de espera."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "cancelamento", "ANAC 400", "três opções", "reembolso",
            "reacomodação", "outra modalidade", "72 horas", "direito"
        ],
    },
    {
        "id": "pol_006",
        "titulo": "Overbooking - Preterição de Embarque",
        "conteudo": (
            "Quando ocorre overbooking (venda de assentos além da capacidade), "
            "a companhia deve primeiro procurar voluntários dispostos a ceder "
            "seus lugares em troca de compensação negociada (dinheiro, milhas, "
            "diárias de hotel, upgrade). Se não houver voluntários suficientes, "
            "o passageiro preterido involuntariamente tem direito a: "
            "compensação financeira imediata no valor de 250 DES (voos "
            "domésticos até 1.100 km) ou 500 DES (voos acima de 1.100 km), "
            "além de reacomodação no próximo voo ou reembolso integral. "
            "A assistência material também é devida durante todo o período "
            "de espera."
        ),
        "categoria": "overbooking",
        "palavras_chave": [
            "overbooking", "preterição", "compensação", "voluntário",
            "DES", "embarque negado", "excesso de passageiros"
        ],
    },
    {
        "id": "pol_007",
        "titulo": "Bagagem Extraviada - Prazos e Indenização",
        "conteudo": (
            "Em caso de extravio de bagagem, a companhia aérea deve localizar "
            "a mala em até 7 dias (voos domésticos) ou 21 dias (voos "
            "internacionais). Se a bagagem não for localizada dentro desse "
            "prazo, considera-se definitivamente extraviada e o passageiro "
            "tem direito a indenização. O valor máximo de indenização é de "
            "1.131 DES para voos internacionais (Convenção de Montreal). "
            "Para voos domésticos, o limite é de R$ 4.000 por passageiro. "
            "O passageiro deve registrar o Relatório de Irregularidade de "
            "Bagagem (RIB) no balcão da companhia ainda no aeroporto. "
            "Despesas emergenciais com roupas e itens de higiene devem ser "
            "reembolsadas mediante apresentação de notas fiscais."
        ),
        "categoria": "bagagem",
        "palavras_chave": [
            "bagagem", "extravio", "mala", "indenização",
            "7 dias", "21 dias", "RIB", "Montreal"
        ],
    },
    {
        "id": "pol_008",
        "titulo": "Condições Meteorológicas e Força Maior",
        "conteudo": (
            "Em situações de força maior (condições meteorológicas adversas, "
            "fechamento de aeroporto, restrição do espaço aéreo), a companhia "
            "aérea não é obrigada a pagar indenização por danos morais, mas "
            "permanece obrigada a oferecer assistência material conforme os "
            "prazos da Resolução ANAC 400 (comunicação a partir de 1h, "
            "alimentação a partir de 2h, hospedagem a partir de 4h). "
            "O passageiro mantém o direito de escolha entre reembolso, "
            "reacomodação ou execução por outra modalidade. A companhia "
            "deve manter o passageiro informado sobre a previsão de "
            "normalização das operações e atualizar as informações a cada "
            "30 minutos durante a interrupção."
        ),
        "categoria": "clima",
        "palavras_chave": [
            "meteorologia", "força maior", "tempestade", "clima",
            "aeroporto fechado", "condições adversas", "mau tempo"
        ],
    },
    {
        "id": "pol_009",
        "titulo": "Alteração de Voo pelo Passageiro",
        "conteudo": (
            "Caso o passageiro deseje alterar a data ou horário do voo, "
            "a possibilidade depende das regras tarifárias do bilhete "
            "adquirido. Tarifas promocionais podem não permitir alteração "
            "ou cobrar taxa de remarcação. O passageiro pode desistir da "
            "passagem em até 24 horas após a compra, sem qualquer ônus, "
            "desde que a compra tenha sido feita com antecedência mínima "
            "de 7 dias da data do voo, conforme Resolução ANAC 400, "
            "artigo 11."
        ),
        "categoria": "reembolso",
        "palavras_chave": [
            "alteração", "remarcação", "desistência", "24 horas",
            "taxa", "tarifa", "prazo"
        ],
    },
    {
        "id": "pol_010",
        "titulo": "Direitos de Passageiros com Necessidades Especiais",
        "conteudo": (
            "Passageiros com deficiência ou mobilidade reduzida têm direito "
            "a atendimento prioritário em todas as situações de crise. "
            "A companhia deve garantir acessibilidade no processo de "
            "reacomodação, incluindo assistência especial no embarque e "
            "desembarque. Em caso de preterição, passageiros com necessidades "
            "especiais devem ser os últimos a serem involuntariamente "
            "preteridos. A assistência material deve considerar as "
            "necessidades específicas do passageiro, como dieta especial "
            "ou medicamentos refrigerados."
        ),
        "categoria": "direitos",
        "palavras_chave": [
            "deficiência", "mobilidade reduzida", "acessibilidade",
            "prioridade", "necessidades especiais", "atendimento"
        ],
    },
]
