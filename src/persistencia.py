"""
Módulo de persistência para histórico de sessões.

Implementa checkpointer SQLite para persistir conversas entre reinicializações
do servidor, substituindo o MemorySaver in-memory para sessões que necessitam
de histórico permanente.
"""

import os
import json
import sqlite3
import threading
from datetime import datetime
from typing import Optional


# Diretório padrão para o banco de dados
_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_DB_PATH = os.path.join(_DB_DIR, "sessoes.db")


class GerenciadorSessoes:
    """Gerencia sessões de usuários com persistência SQLite.

    Armazena metadados de sessão, histórico de interações e
    estado do último processamento para cada thread_id.

    Thread-safe para uso com Gradio em modo multi-sessão.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Inicializa o gerenciador de sessões.

        Args:
            db_path: Caminho para o arquivo SQLite. Se None, usa o padrão.
        """
        self.db_path = db_path or _DB_PATH
        self._lock = threading.Lock()
        self._inicializar_db()

    def _inicializar_db(self):
        """Cria as tabelas se não existirem."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS sessoes (
                        thread_id TEXT PRIMARY KEY,
                        criada_em TEXT NOT NULL,
                        ultima_atividade TEXT NOT NULL,
                        total_interacoes INTEGER DEFAULT 0,
                        codigo_reserva TEXT DEFAULT '',
                        tenant_id TEXT DEFAULT 'default',
                        usuario_id TEXT DEFAULT '',
                        metadata TEXT DEFAULT '{}'
                    );

                    CREATE TABLE IF NOT EXISTS historico (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        thread_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (thread_id) REFERENCES sessoes(thread_id)
                    );

                    CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        thread_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        rating INTEGER,
                        comentario TEXT DEFAULT '',
                        mensagem_id INTEGER,
                        FOREIGN KEY (thread_id) REFERENCES sessoes(thread_id)
                    );

                    CREATE TABLE IF NOT EXISTS analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        evento TEXT NOT NULL,
                        thread_id TEXT DEFAULT '',
                        tenant_id TEXT DEFAULT 'default',
                        dados TEXT DEFAULT '{}',
                        tempo_resposta_ms INTEGER DEFAULT 0
                    );

                    CREATE INDEX IF NOT EXISTS idx_historico_thread
                        ON historico(thread_id);
                    CREATE INDEX IF NOT EXISTS idx_historico_timestamp
                        ON historico(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_analytics_evento
                        ON analytics(evento);
                    CREATE INDEX IF NOT EXISTS idx_analytics_tenant
                        ON analytics(tenant_id);
                    CREATE INDEX IF NOT EXISTS idx_sessoes_tenant
                        ON sessoes(tenant_id);
                """)
                conn.commit()
            finally:
                conn.close()

    def criar_sessao(self, thread_id: str, tenant_id: str = "default",
                     usuario_id: str = "") -> dict:
        """Cria uma nova sessão ou retorna a existente.

        Args:
            thread_id: Identificador único da sessão/conversa.
            tenant_id: ID do tenant (para multi-tenant B2B).
            usuario_id: ID do usuário autenticado (se houver).

        Returns:
            Dict com dados da sessão.
        """
        agora = datetime.now().isoformat()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    "SELECT * FROM sessoes WHERE thread_id = ?", (thread_id,)
                )
                row = cursor.fetchone()
                if row:
                    # Atualizar última atividade
                    conn.execute(
                        "UPDATE sessoes SET ultima_atividade = ? WHERE thread_id = ?",
                        (agora, thread_id)
                    )
                    conn.commit()
                    return {
                        "thread_id": row[0],
                        "criada_em": row[1],
                        "ultima_atividade": agora,
                        "total_interacoes": row[3],
                        "codigo_reserva": row[4],
                        "tenant_id": row[5],
                        "usuario_id": row[6],
                    }
                else:
                    conn.execute(
                        """INSERT INTO sessoes
                        (thread_id, criada_em, ultima_atividade, tenant_id, usuario_id)
                        VALUES (?, ?, ?, ?, ?)""",
                        (thread_id, agora, agora, tenant_id, usuario_id)
                    )
                    conn.commit()
                    return {
                        "thread_id": thread_id,
                        "criada_em": agora,
                        "ultima_atividade": agora,
                        "total_interacoes": 0,
                        "codigo_reserva": "",
                        "tenant_id": tenant_id,
                        "usuario_id": usuario_id,
                    }
            finally:
                conn.close()

    def registrar_interacao(self, thread_id: str, role: str, content: str,
                            metadata: Optional[dict] = None):
        """Registra uma mensagem no histórico.

        Args:
            thread_id: ID da sessão.
            role: "human" ou "ai".
            content: Conteúdo da mensagem.
            metadata: Dados adicionais (opcional).
        """
        agora = datetime.now().isoformat()
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    """INSERT INTO historico (thread_id, timestamp, role, content, metadata)
                    VALUES (?, ?, ?, ?, ?)""",
                    (thread_id, agora, role, content, meta_json)
                )
                conn.execute(
                    """UPDATE sessoes
                    SET ultima_atividade = ?, total_interacoes = total_interacoes + 1
                    WHERE thread_id = ?""",
                    (agora, thread_id)
                )
                conn.commit()
            finally:
                conn.close()

    def obter_historico(self, thread_id: str, limite: int = 50) -> list[dict]:
        """Recupera o histórico de mensagens de uma sessão.

        Args:
            thread_id: ID da sessão.
            limite: Número máximo de mensagens a retornar.

        Returns:
            Lista de dicts com role, content, timestamp.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """SELECT role, content, timestamp, metadata FROM historico
                    WHERE thread_id = ?
                    ORDER BY timestamp DESC LIMIT ?""",
                    (thread_id, limite)
                )
                rows = cursor.fetchall()
                return [
                    {
                        "role": row[0],
                        "content": row[1],
                        "timestamp": row[2],
                        "metadata": json.loads(row[3]) if row[3] else {},
                    }
                    for row in reversed(rows)
                ]
            finally:
                conn.close()

    def atualizar_codigo_reserva(self, thread_id: str, codigo: str):
        """Atualiza o código de reserva associado à sessão."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    "UPDATE sessoes SET codigo_reserva = ? WHERE thread_id = ?",
                    (codigo, thread_id)
                )
                conn.commit()
            finally:
                conn.close()

    def registrar_feedback(self, thread_id: str, rating: int,
                           comentario: str = "", mensagem_id: Optional[int] = None):
        """Registra feedback do usuário sobre uma resposta.

        Args:
            thread_id: ID da sessão.
            rating: Nota de 1 a 5.
            comentario: Texto livre do usuário.
            mensagem_id: ID da mensagem avaliada (opcional).
        """
        agora = datetime.now().isoformat()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    """INSERT INTO feedback (thread_id, timestamp, rating, comentario, mensagem_id)
                    VALUES (?, ?, ?, ?, ?)""",
                    (thread_id, agora, rating, comentario, mensagem_id)
                )
                conn.commit()
            finally:
                conn.close()

    def registrar_evento_analytics(self, evento: str, thread_id: str = "",
                                   tenant_id: str = "default",
                                   dados: Optional[dict] = None,
                                   tempo_resposta_ms: int = 0):
        """Registra um evento de analytics.

        Args:
            evento: Tipo do evento (ex: 'crise_resolvida', 'consulta_clima').
            thread_id: ID da sessão (opcional).
            tenant_id: ID do tenant.
            dados: Dados adicionais do evento.
            tempo_resposta_ms: Tempo de resposta em milissegundos.
        """
        agora = datetime.now().isoformat()
        dados_json = json.dumps(dados or {}, ensure_ascii=False)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    """INSERT INTO analytics
                    (timestamp, evento, thread_id, tenant_id, dados, tempo_resposta_ms)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (agora, evento, thread_id, tenant_id, dados_json, tempo_resposta_ms)
                )
                conn.commit()
            finally:
                conn.close()

    def obter_analytics_resumo(self, tenant_id: str = "default",
                               dias: int = 7) -> dict:
        """Obtém resumo de analytics para o dashboard.

        Args:
            tenant_id: Filtrar por tenant.
            dias: Número de dias para o período de análise.

        Returns:
            Dict com métricas agregadas.
        """
        from datetime import timedelta
        data_inicio = (datetime.now() - timedelta(days=dias)).isoformat()

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Total de sessões no período
                cursor = conn.execute(
                    """SELECT COUNT(*) FROM sessoes
                    WHERE tenant_id = ? AND criada_em >= ?""",
                    (tenant_id, data_inicio)
                )
                total_sessoes = cursor.fetchone()[0]

                # Total de interações
                cursor = conn.execute(
                    """SELECT COUNT(*) FROM historico h
                    JOIN sessoes s ON h.thread_id = s.thread_id
                    WHERE s.tenant_id = ? AND h.timestamp >= ?""",
                    (tenant_id, data_inicio)
                )
                total_interacoes = cursor.fetchone()[0]

                # Eventos por tipo
                cursor = conn.execute(
                    """SELECT evento, COUNT(*) FROM analytics
                    WHERE tenant_id = ? AND timestamp >= ?
                    GROUP BY evento ORDER BY COUNT(*) DESC""",
                    (tenant_id, data_inicio)
                )
                eventos = {row[0]: row[1] for row in cursor.fetchall()}

                # Tempo médio de resposta
                cursor = conn.execute(
                    """SELECT AVG(tempo_resposta_ms) FROM analytics
                    WHERE tenant_id = ? AND timestamp >= ?
                    AND tempo_resposta_ms > 0""",
                    (tenant_id, data_inicio)
                )
                tempo_medio = cursor.fetchone()[0] or 0

                # Média de feedback
                cursor = conn.execute(
                    """SELECT AVG(rating), COUNT(*) FROM feedback f
                    JOIN sessoes s ON f.thread_id = s.thread_id
                    WHERE s.tenant_id = ? AND f.timestamp >= ?""",
                    (tenant_id, data_inicio)
                )
                row = cursor.fetchone()
                media_feedback = row[0] or 0
                total_feedbacks = row[1] or 0

                return {
                    "periodo_dias": dias,
                    "tenant_id": tenant_id,
                    "total_sessoes": total_sessoes,
                    "total_interacoes": total_interacoes,
                    "eventos_por_tipo": eventos,
                    "tempo_medio_resposta_ms": round(tempo_medio, 2),
                    "media_feedback": round(media_feedback, 2),
                    "total_feedbacks": total_feedbacks,
                }
            finally:
                conn.close()

    def listar_sessoes(self, tenant_id: str = "default",
                       limite: int = 100) -> list[dict]:
        """Lista sessões ativas de um tenant.

        Args:
            tenant_id: ID do tenant.
            limite: Máximo de sessões a retornar.

        Returns:
            Lista de sessões com metadados.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """SELECT thread_id, criada_em, ultima_atividade,
                    total_interacoes, codigo_reserva, usuario_id
                    FROM sessoes WHERE tenant_id = ?
                    ORDER BY ultima_atividade DESC LIMIT ?""",
                    (tenant_id, limite)
                )
                return [
                    {
                        "thread_id": row[0],
                        "criada_em": row[1],
                        "ultima_atividade": row[2],
                        "total_interacoes": row[3],
                        "codigo_reserva": row[4],
                        "usuario_id": row[5],
                    }
                    for row in cursor.fetchall()
                ]
            finally:
                conn.close()


# Instância global (singleton)
_gerenciador: Optional[GerenciadorSessoes] = None


def get_gerenciador(db_path: Optional[str] = None) -> GerenciadorSessoes:
    """Retorna instância singleton do gerenciador de sessões.

    Args:
        db_path: Caminho para o banco. Se None, usa padrão.

    Returns:
        Instância do GerenciadorSessoes.
    """
    global _gerenciador
    if _gerenciador is None:
        _gerenciador = GerenciadorSessoes(db_path)
    return _gerenciador
