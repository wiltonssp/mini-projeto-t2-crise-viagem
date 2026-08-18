"""
Módulo de embeddings semânticos para busca aprimorada.

v2.0: Implementa busca com Sentence Transformers como alternativa
mais precisa ao TF-IDF, com fallback automático para TF-IDF caso
o modelo não esteja disponível.
"""

import logging
from typing import Optional

import numpy as np

from src.rag.busca import BuscaSemantica

logger = logging.getLogger(__name__)

# Flag global para indicar se sentence-transformers está disponível
_SENTENCE_TRANSFORMERS_DISPONIVEL = False
_modelo_embeddings = None

try:
    from sentence_transformers import SentenceTransformer
    _SENTENCE_TRANSFORMERS_DISPONIVEL = True
except ImportError:
    logger.info(
        "sentence-transformers não instalado — usando TF-IDF como fallback. "
        "Para embeddings semânticos: pip install sentence-transformers"
    )


class BuscaEmbeddings:
    """Busca semântica com Sentence Transformers.

    Usa embeddings densos para encontrar documentos relevantes com
    melhor compreensão semântica que TF-IDF.

    Fallback automático para BuscaSemantica (TF-IDF) se o modelo
    de embeddings não estiver disponível.

    Attributes:
        documentos: Lista de documentos com campos 'conteudo' e 'palavras_chave'.
        modelo_nome: Nome do modelo Sentence Transformers a usar.
        limiar: Score mínimo para incluir resultado.
    """

    # Modelos recomendados (multilíngue para PT-BR):
    MODELO_PADRAO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    MODELO_ALTERNATIVO = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, documentos: list[dict], limiar: float = 0.3,
                 modelo_nome: Optional[str] = None):
        """Inicializa a busca por embeddings.

        Args:
            documentos: Lista de dicts com campos 'conteudo' e 'palavras_chave'.
            limiar: Score mínimo de similaridade (0.0 a 1.0). Default: 0.3.
            modelo_nome: Nome do modelo (default: multilíngue MiniLM).
        """
        self.documentos = documentos
        self.limiar = limiar
        self.modelo_nome = modelo_nome or self.MODELO_PADRAO
        self._modelo = None
        self._embeddings_documentos = None
        self._fallback = None

        if _SENTENCE_TRANSFORMERS_DISPONIVEL:
            try:
                self._inicializar_modelo()
            except Exception as e:
                logger.warning("Falha ao carregar modelo de embeddings: %s", e)
                self._inicializar_fallback()
        else:
            self._inicializar_fallback()

    def _inicializar_modelo(self):
        """Carrega o modelo e pré-computa embeddings dos documentos."""
        global _modelo_embeddings

        # Reutilizar modelo global se já carregado (evitar reload)
        if _modelo_embeddings is None:
            from sentence_transformers import SentenceTransformer
            _modelo_embeddings = SentenceTransformer(self.modelo_nome)
            logger.info("Modelo de embeddings carregado: %s", self.modelo_nome)

        self._modelo = _modelo_embeddings

        # Pré-computar embeddings dos documentos
        textos = [
            doc["conteudo"] + " " + " ".join(doc.get("palavras_chave", []))
            for doc in self.documentos
        ]
        self._embeddings_documentos = self._modelo.encode(
            textos, convert_to_numpy=True, normalize_embeddings=True
        )

    def _inicializar_fallback(self):
        """Inicializa o TF-IDF como fallback."""
        self._fallback = BuscaSemantica(self.documentos, limiar=0.1)
        logger.info("Usando TF-IDF como fallback para busca semântica")

    @property
    def usando_embeddings(self) -> bool:
        """Indica se está usando embeddings ou TF-IDF fallback."""
        return self._modelo is not None and self._embeddings_documentos is not None

    def buscar(self, query: str, top_k: int = 5) -> list[dict]:
        """Busca documentos relevantes usando embeddings ou TF-IDF.

        Args:
            query: Texto de busca descrevendo a situação.
            top_k: Número máximo de resultados.

        Returns:
            Lista de documentos com score, ordenados por relevância.
        """
        if self._fallback:
            return self._fallback.buscar(query, top_k)

        try:
            # Computar embedding da query
            query_embedding = self._modelo.encode(
                [query], convert_to_numpy=True, normalize_embeddings=True
            )

            # Calcular similaridade cosseno (já normalizados)
            scores = np.dot(self._embeddings_documentos, query_embedding.T).flatten()

            # Ordenar por score decrescente
            indices_ordenados = np.argsort(scores)[::-1]

            resultados = []
            for idx in indices_ordenados[:top_k]:
                if scores[idx] >= self.limiar:
                    resultados.append({
                        **self.documentos[idx],
                        "score": float(scores[idx]),
                        "metodo": "embeddings",
                    })

            return resultados
        except Exception as e:
            logger.warning("Erro na busca por embeddings, usando fallback: %s", e)
            if not self._fallback:
                self._inicializar_fallback()
            return self._fallback.buscar(query, top_k)


def criar_buscador(documentos: list[dict], limiar: float = 0.3,
                   forcar_tfidf: bool = False) -> BuscaEmbeddings | BuscaSemantica:
    """Factory para criar o buscador mais adequado disponível.

    Args:
        documentos: Lista de documentos para indexar.
        limiar: Score mínimo de similaridade.
        forcar_tfidf: Se True, usa TF-IDF mesmo com embeddings disponíveis.

    Returns:
        Instância de BuscaEmbeddings ou BuscaSemantica.
    """
    if forcar_tfidf or not _SENTENCE_TRANSFORMERS_DISPONIVEL:
        return BuscaSemantica(documentos, limiar=0.1)
    return BuscaEmbeddings(documentos, limiar=limiar)
