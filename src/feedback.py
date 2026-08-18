"""
Sistema de feedback loop para melhoria contínua do LLM.

v3.0: Coleta feedback dos usuários, analisa padrões de insatisfação
e gera datasets para fine-tuning ou ajuste de prompts.
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_DB_PATH = os.path.join(_DB_DIR, "feedback.db")


class SistemaFeedback:
    """Sistema de coleta e análise de feedback para melhoria do LLM.

    Funcionalidades:
    - Coleta de ratings (1-5) e comentários textuais
    - Categorização automática de feedback negativo
    - Geração de datasets para fine-tuning
    - Identificação de padrões de falha
    - Sugestões de melhoria de prompt
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DB_PATH
        self._lock = threading.Lock()
        self._inicializar_db()

    def _inicializar_db(self):
        """Cria tabelas de feedback."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS feedback_detalhado (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        thread_id TEXT NOT NULL,
                        tenant_id TEXT DEFAULT 'default',
                        timestamp TEXT NOT NULL,
                        rating INTEGER NOT NULL,
                        comentario TEXT DEFAULT '',
                        categoria TEXT DEFAULT '',
                        mensagem_usuario TEXT DEFAULT '',
                        resposta_agente TEXT DEFAULT '',
                        contexto TEXT DEFAULT '{}',
                        resolvido INTEGER DEFAULT 0,
                        acao_tomada TEXT DEFAULT ''
                    );

                    CREATE TABLE IF NOT EXISTS padroes_falha (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        padrao TEXT NOT NULL,
                        descricao TEXT DEFAULT '',
                        frequencia INTEGER DEFAULT 1,
                        primeira_ocorrencia TEXT NOT NULL,
                        ultima_ocorrencia TEXT NOT NULL,
                        sugestao_correcao TEXT DEFAULT '',
                        corrigido INTEGER DEFAULT 0
                    );

                    CREATE TABLE IF NOT EXISTS dataset_finetuning (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        input_text TEXT NOT NULL,
                        expected_output TEXT NOT NULL,
                        actual_output TEXT DEFAULT '',
                        quality_score REAL DEFAULT 0.0,
                        tenant_id TEXT DEFAULT 'default',
                        criado_em TEXT NOT NULL,
                        usado_em_treino INTEGER DEFAULT 0
                    );

                    CREATE INDEX IF NOT EXISTS idx_feedback_rating
                        ON feedback_detalhado(rating);
                    CREATE INDEX IF NOT EXISTS idx_feedback_tenant
                        ON feedback_detalhado(tenant_id);
                    CREATE INDEX IF NOT EXISTS idx_feedback_categoria
                        ON feedback_detalhado(categoria);
                """)
                conn.commit()
            finally:
                conn.close()

    def registrar_feedback(self, thread_id: str, rating: int,
                           comentario: str = "",
                           mensagem_usuario: str = "",
                           resposta_agente: str = "",
                           tenant_id: str = "default",
                           contexto: Optional[dict] = None) -> int:
        """Registra feedback detalhado do usuário.

        Args:
            thread_id: ID da sessão.
            rating: Nota de 1 a 5.
            comentario: Texto livre do usuário.
            mensagem_usuario: Mensagem original que gerou a resposta.
            resposta_agente: Resposta do agente avaliada.
            tenant_id: ID do tenant.
            contexto: Dados adicionais (código de reserva, tipo de crise, etc.)

        Returns:
            ID do feedback registrado.
        """
        agora = datetime.now().isoformat()
        categoria = self._categorizar_feedback(rating, comentario)
        contexto_json = json.dumps(contexto or {}, ensure_ascii=False)

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """INSERT INTO feedback_detalhado
                    (thread_id, tenant_id, timestamp, rating, comentario,
                     categoria, mensagem_usuario, resposta_agente, contexto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (thread_id, tenant_id, agora, rating, comentario,
                     categoria, mensagem_usuario, resposta_agente, contexto_json)
                )
                feedback_id = cursor.lastrowid
                conn.commit()

                # Se feedback negativo, analisar padrão
                if rating <= 2:
                    self._registrar_padrao_falha(
                        conn, mensagem_usuario, resposta_agente, categoria
                    )

                return feedback_id
            finally:
                conn.close()

    def _categorizar_feedback(self, rating: int, comentario: str) -> str:
        """Categoriza automaticamente o feedback baseado no rating e comentário."""
        if rating >= 4:
            return "positivo"

        comentario_lower = comentario.lower()

        categorias = {
            "resposta_incorreta": [
                "errado", "incorreto", "falso", "mentira", "inventou",
                "wrong", "incorrect", "fabricated",
            ],
            "resposta_incompleta": [
                "incompleto", "faltou", "mais informação", "insuficiente",
                "incomplete", "missing",
            ],
            "resposta_generica": [
                "genérico", "generica", "vago", "não personalizou",
                "generic", "vague",
            ],
            "resposta_lenta": [
                "demorou", "lento", "demora", "slow",
            ],
            "nao_entendeu": [
                "não entendeu", "nao entendeu", "confuso", "errou pergunta",
                "misunderstood",
            ],
            "direitos_incorretos": [
                "direitos errados", "lei errada", "regulamento incorreto",
                "wrong rights",
            ],
        }

        for categoria, palavras in categorias.items():
            for palavra in palavras:
                if palavra in comentario_lower:
                    return categoria

        if rating <= 2:
            return "negativo_geral"
        return "neutro"

    def _registrar_padrao_falha(self, conn: sqlite3.Connection,
                                 mensagem: str, resposta: str,
                                 categoria: str):
        """Registra ou atualiza padrão de falha identificado."""
        agora = datetime.now().isoformat()

        # Verificar se padrão similar já existe
        cursor = conn.execute(
            "SELECT id, frequencia FROM padroes_falha WHERE padrao = ?",
            (categoria,)
        )
        row = cursor.fetchone()

        if row:
            conn.execute(
                """UPDATE padroes_falha
                SET frequencia = frequencia + 1, ultima_ocorrencia = ?
                WHERE id = ?""",
                (agora, row[0])
            )
        else:
            conn.execute(
                """INSERT INTO padroes_falha
                (padrao, descricao, primeira_ocorrencia, ultima_ocorrencia)
                VALUES (?, ?, ?, ?)""",
                (categoria, f"Padrão detectado: {categoria}", agora, agora)
            )
        conn.commit()

    def adicionar_exemplo_finetuning(self, input_text: str,
                                      expected_output: str,
                                      actual_output: str = "",
                                      quality_score: float = 1.0,
                                      tenant_id: str = "default") -> int:
        """Adiciona exemplo ao dataset de fine-tuning.

        Args:
            input_text: Entrada (mensagem do usuário + contexto).
            expected_output: Saída esperada (resposta ideal).
            actual_output: Saída real do modelo (para comparação).
            quality_score: Score de qualidade (0.0 a 1.0).
            tenant_id: ID do tenant.

        Returns:
            ID do exemplo adicionado.
        """
        agora = datetime.now().isoformat()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """INSERT INTO dataset_finetuning
                    (input_text, expected_output, actual_output,
                     quality_score, tenant_id, criado_em)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (input_text, expected_output, actual_output,
                     quality_score, tenant_id, agora)
                )
                conn.commit()
                return cursor.lastrowid
            finally:
                conn.close()

    def exportar_dataset_finetuning(self, tenant_id: str = "default",
                                     min_quality: float = 0.7,
                                     formato: str = "jsonl") -> str:
        """Exporta dataset de fine-tuning.

        Args:
            tenant_id: Filtrar por tenant.
            min_quality: Score mínimo de qualidade para incluir.
            formato: Formato de saída ('jsonl' ou 'json').

        Returns:
            String com o dataset no formato solicitado.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """SELECT input_text, expected_output, quality_score
                    FROM dataset_finetuning
                    WHERE tenant_id = ? AND quality_score >= ?
                    AND usado_em_treino = 0
                    ORDER BY quality_score DESC""",
                    (tenant_id, min_quality)
                )

                exemplos = []
                for row in cursor.fetchall():
                    exemplos.append({
                        "messages": [
                            {"role": "user", "content": row[0]},
                            {"role": "assistant", "content": row[1]},
                        ],
                        "quality_score": row[2],
                    })

                if formato == "jsonl":
                    return "\n".join(json.dumps(ex, ensure_ascii=False) for ex in exemplos)
                return json.dumps(exemplos, ensure_ascii=False, indent=2)
            finally:
                conn.close()

    def obter_resumo_feedback(self, tenant_id: str = "default",
                               dias: int = 30) -> dict:
        """Obtém resumo estatístico do feedback.

        Args:
            tenant_id: ID do tenant.
            dias: Período em dias.

        Returns:
            Dict com estatísticas de feedback.
        """
        from datetime import timedelta
        data_inicio = (datetime.now() - timedelta(days=dias)).isoformat()

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Distribuição de ratings
                cursor = conn.execute(
                    """SELECT rating, COUNT(*) FROM feedback_detalhado
                    WHERE tenant_id = ? AND timestamp >= ?
                    GROUP BY rating ORDER BY rating""",
                    (tenant_id, data_inicio)
                )
                distribuicao = {row[0]: row[1] for row in cursor.fetchall()}

                # Média geral
                cursor = conn.execute(
                    """SELECT AVG(rating), COUNT(*) FROM feedback_detalhado
                    WHERE tenant_id = ? AND timestamp >= ?""",
                    (tenant_id, data_inicio)
                )
                row = cursor.fetchone()
                media = row[0] or 0
                total = row[1] or 0

                # Categorias de feedback negativo
                cursor = conn.execute(
                    """SELECT categoria, COUNT(*) FROM feedback_detalhado
                    WHERE tenant_id = ? AND timestamp >= ? AND rating <= 2
                    GROUP BY categoria ORDER BY COUNT(*) DESC""",
                    (tenant_id, data_inicio)
                )
                categorias_negativas = {row[0]: row[1] for row in cursor.fetchall()}

                # Padrões de falha ativos
                cursor = conn.execute(
                    """SELECT padrao, frequencia, sugestao_correcao
                    FROM padroes_falha WHERE corrigido = 0
                    ORDER BY frequencia DESC LIMIT 10"""
                )
                padroes = [
                    {
                        "padrao": row[0],
                        "frequencia": row[1],
                        "sugestao": row[2],
                    }
                    for row in cursor.fetchall()
                ]

                # Total de exemplos de fine-tuning
                cursor = conn.execute(
                    """SELECT COUNT(*) FROM dataset_finetuning
                    WHERE tenant_id = ? AND usado_em_treino = 0""",
                    (tenant_id,)
                )
                exemplos_pendentes = cursor.fetchone()[0]

                return {
                    "periodo_dias": dias,
                    "total_feedbacks": total,
                    "media_rating": round(media, 2),
                    "distribuicao_ratings": distribuicao,
                    "categorias_negativas": categorias_negativas,
                    "padroes_falha_ativos": padroes,
                    "exemplos_finetuning_pendentes": exemplos_pendentes,
                    "taxa_satisfacao": round(
                        (distribuicao.get(4, 0) + distribuicao.get(5, 0)) / max(total, 1) * 100, 1
                    ),
                }
            finally:
                conn.close()

    def sugerir_melhorias_prompt(self, tenant_id: str = "default") -> list[dict]:
        """Analisa feedback negativo e sugere melhorias no prompt do sistema.

        Args:
            tenant_id: ID do tenant.

        Returns:
            Lista de sugestões com prioridade e descrição.
        """
        resumo = self.obter_resumo_feedback(tenant_id)
        sugestoes = []

        categorias = resumo.get("categorias_negativas", {})

        if categorias.get("resposta_generica", 0) > 3:
            sugestoes.append({
                "prioridade": "alta",
                "area": "personalização",
                "sugestao": (
                    "Reforçar no prompt a necessidade de referenciar dados específicos "
                    "do viajante (número do voo, destino, horários) em todas as seções."
                ),
                "frequencia": categorias["resposta_generica"],
            })

        if categorias.get("resposta_incompleta", 0) > 3:
            sugestoes.append({
                "prioridade": "alta",
                "area": "completude",
                "sugestao": (
                    "Adicionar instrução no prompt para verificar se todas as 5 seções "
                    "do plano foram preenchidas com informações substantivas."
                ),
                "frequencia": categorias["resposta_incompleta"],
            })

        if categorias.get("direitos_incorretos", 0) > 2:
            sugestoes.append({
                "prioridade": "critica",
                "area": "precisão_juridica",
                "sugestao": (
                    "Expandir a base RAG com mais documentos da ANAC e CDC. "
                    "Considerar adicionar validação cruzada de informações legais."
                ),
                "frequencia": categorias["direitos_incorretos"],
            })

        if categorias.get("nao_entendeu", 0) > 3:
            sugestoes.append({
                "prioridade": "media",
                "area": "compreensão",
                "sugestao": (
                    "Melhorar a extração de intenção no nó de validação. "
                    "Considerar adicionar exemplos few-shot no prompt."
                ),
                "frequencia": categorias["nao_entendeu"],
            })

        if categorias.get("resposta_lenta", 0) > 5:
            sugestoes.append({
                "prioridade": "media",
                "area": "performance",
                "sugestao": (
                    "Considerar paralelizar consultas de voo, clima e transporte. "
                    "Avaliar uso de modelo menor para perguntas simples."
                ),
                "frequencia": categorias["resposta_lenta"],
            })

        return sorted(sugestoes, key=lambda x: {"critica": 0, "alta": 1, "media": 2}.get(x["prioridade"], 3))


# Instância singleton
_sistema_feedback: Optional[SistemaFeedback] = None


def get_sistema_feedback(db_path: Optional[str] = None) -> SistemaFeedback:
    """Retorna instância singleton do sistema de feedback."""
    global _sistema_feedback
    if _sistema_feedback is None:
        _sistema_feedback = SistemaFeedback(db_path)
    return _sistema_feedback
