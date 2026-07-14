"""Módulo de busca semântica para recuperação de políticas e legislação.

Implementa busca baseada em TF-IDF com similaridade cosseno para
encontrar documentos relevantes à situação do viajante.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class BuscaSemantica:
    """Busca semântica em documentos usando TF-IDF e similaridade cosseno.

    Attributes:
        documentos: Lista de documentos, cada um com campos 'conteudo' e 'palavras_chave'.
        limiar: Score mínimo de similaridade para incluir um documento nos resultados.
        vectorizer: TfidfVectorizer configurado para o corpus.
        matrix: Matriz TF-IDF dos documentos.
    """

    def __init__(self, documentos: list[dict], limiar: float = 0.1):
        """Inicializa a busca semântica com os documentos fornecidos.

        Args:
            documentos: Lista de dicts com campos 'conteudo' e 'palavras_chave'.
            limiar: Score mínimo de similaridade (0.0 a 1.0). Default: 0.1.
        """
        self.documentos = documentos
        self.limiar = limiar
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=5000
        )
        # Combina conteúdo + palavras-chave para vetorização
        textos = [
            doc["conteudo"] + " " + " ".join(doc["palavras_chave"])
            for doc in documentos
        ]
        self.matrix = self.vectorizer.fit_transform(textos)

    def buscar(self, query: str, top_k: int = 5) -> list[dict]:
        """Busca documentos relevantes para a query.

        Args:
            query: Texto de busca descrevendo a situação do viajante.
            top_k: Número máximo de resultados a retornar. Default: 5.

        Returns:
            Lista de documentos com score >= limiar, ordenados por relevância
            decrescente. Cada resultado inclui todos os campos do documento
            original mais o campo 'score' com o valor float da similaridade.
        """
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()

        resultados = []
        indices_ordenados = np.argsort(scores)[::-1]

        for idx in indices_ordenados[:top_k]:
            if scores[idx] >= self.limiar:
                resultados.append({
                    **self.documentos[idx],
                    "score": float(scores[idx])
                })

        return resultados
