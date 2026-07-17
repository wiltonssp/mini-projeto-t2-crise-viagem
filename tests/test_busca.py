"""Testes unitários para o módulo de busca semântica."""

from src.rag.busca import BuscaSemantica


# Documentos de teste simulando a base de políticas
DOCS_TESTE = [
    {
        "id": "pol_001",
        "titulo": "Política de Reembolso - Voos Cancelados",
        "conteudo": (
            "Em caso de cancelamento de voo pela companhia, o passageiro "
            "tem direito a reembolso integral do valor pago, incluindo "
            "taxas, em até 7 dias úteis. Alternativamente, pode optar "
            "por reacomodação no próximo voo disponível sem custo adicional."
        ),
        "categoria": "reembolso",
        "palavras_chave": ["cancelamento", "reembolso", "devolução", "valor"]
    },
    {
        "id": "pol_002",
        "titulo": "Direitos do Passageiro - Resolução ANAC 400",
        "conteudo": (
            "Conforme Resolução 400 da ANAC: atrasos superiores a 1 hora "
            "garantem comunicação gratuita; superiores a 2 horas garantem "
            "alimentação; superiores a 4 horas garantem hospedagem e "
            "transporte. Em cancelamentos, o passageiro escolhe entre "
            "reembolso, reacomodação ou execução por outra modalidade."
        ),
        "categoria": "direitos",
        "palavras_chave": ["atraso", "ANAC", "direito", "assistência"]
    },
    {
        "id": "pol_003",
        "titulo": "Assistência Material em Atrasos",
        "conteudo": (
            "A companhia deve fornecer assistência material proporcional "
            "ao tempo de espera: comunicação após 1 hora, alimentação "
            "após 2 horas, e acomodação após 4 horas de atraso."
        ),
        "categoria": "assistencia",
        "palavras_chave": ["assistência", "material", "alimentação", "acomodação"]
    },
    {
        "id": "pol_004",
        "titulo": "Política de Bagagem Extraviada",
        "conteudo": (
            "Em caso de extravio de bagagem, o passageiro deve registrar "
            "o RIB no aeroporto. A companhia tem até 7 dias para voos "
            "domésticos e 21 dias para internacionais para localizar a bagagem."
        ),
        "categoria": "bagagem",
        "palavras_chave": ["bagagem", "extravio", "mala", "RIB"]
    },
]


class TestBuscaSemantica:
    """Testes para a classe BuscaSemantica."""

    def test_inicializacao(self):
        """Verifica que a instância é criada sem erros."""
        busca = BuscaSemantica(DOCS_TESTE)
        assert busca.documentos == DOCS_TESTE
        assert busca.limiar == 0.1
        assert busca.matrix is not None

    def test_inicializacao_limiar_customizado(self):
        """Verifica limiar customizado."""
        busca = BuscaSemantica(DOCS_TESTE, limiar=0.5)
        assert busca.limiar == 0.5

    def test_busca_retorna_resultados_relevantes(self):
        """Busca por 'reembolso cancelamento' deve retornar doc de reembolso."""
        busca = BuscaSemantica(DOCS_TESTE)
        resultados = busca.buscar("reembolso cancelamento voo")
        assert len(resultados) > 0
        # O documento de reembolso deve aparecer nos resultados
        ids = [r["id"] for r in resultados]
        assert "pol_001" in ids

    def test_busca_retorna_score(self):
        """Cada resultado deve conter campo 'score' como float."""
        busca = BuscaSemantica(DOCS_TESTE)
        resultados = busca.buscar("atraso direitos passageiro")
        for r in resultados:
            assert "score" in r
            assert isinstance(r["score"], float)
            assert r["score"] >= 0.1  # Acima do limiar

    def test_busca_ordenada_por_score_decrescente(self):
        """Resultados devem estar ordenados por score decrescente."""
        busca = BuscaSemantica(DOCS_TESTE)
        resultados = busca.buscar("cancelamento reembolso direito passageiro")
        scores = [r["score"] for r in resultados]
        assert scores == sorted(scores, reverse=True)

    def test_busca_respeita_top_k(self):
        """Número de resultados não excede top_k."""
        busca = BuscaSemantica(DOCS_TESTE)
        resultados = busca.buscar("voo passageiro", top_k=2)
        assert len(resultados) <= 2

    def test_busca_respeita_limiar(self):
        """Resultados com score abaixo do limiar não são retornados."""
        busca = BuscaSemantica(DOCS_TESTE, limiar=0.9)
        resultados = busca.buscar("algo completamente não relacionado xyz abc")
        # Com limiar alto, poucos ou nenhum resultado
        for r in resultados:
            assert r["score"] >= 0.9

    def test_busca_retorna_todos_campos_documento(self):
        """Resultado preserva todos os campos originais do documento."""
        busca = BuscaSemantica(DOCS_TESTE)
        resultados = busca.buscar("bagagem extraviada mala")
        assert len(resultados) > 0
        resultado = resultados[0]
        assert "id" in resultado
        assert "titulo" in resultado
        assert "conteudo" in resultado
        assert "categoria" in resultado
        assert "palavras_chave" in resultado
        assert "score" in resultado

    def test_busca_sem_resultados_acima_limiar(self):
        """Query irrelevante com limiar alto retorna lista vazia."""
        busca = BuscaSemantica(DOCS_TESTE, limiar=0.99)
        resultados = busca.buscar("programação python javascript")
        assert resultados == []

    def test_busca_bagagem(self):
        """Busca por bagagem deve retornar documento sobre extravio."""
        busca = BuscaSemantica(DOCS_TESTE)
        resultados = busca.buscar("minha mala foi extraviada bagagem perdida")
        assert len(resultados) > 0
        ids = [r["id"] for r in resultados]
        assert "pol_004" in ids
