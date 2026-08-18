"""
Módulo de observabilidade do agente de gestão de crises.

Implementa:
- Logs estruturados em formato JSON (sinal 1)
- Registro de auditoria com trace_id correlacionado (sinal 2)
- Métricas de latência por nó
- Capacidade de investigar e reconstruir uma execução completa

Os dois sinais (logs + auditoria) são correlacionados pelo trace_id,
permitindo rastrear uma execução ponta a ponta.
"""

import json
import logging
import os
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Sinal 1: Logs Estruturados (JSON)
# ---------------------------------------------------------------------------


class JsonFormatter(logging.Formatter):
    """Formatter que produz logs em formato JSON estruturado."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Adicionar campos extras se disponíveis
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "node"):
            log_data["node"] = record.node
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type

        return json.dumps(log_data, ensure_ascii=False)


def configurar_logging_estruturado(nivel: int = logging.INFO) -> logging.Logger:
    """Configura o logging com formato JSON estruturado.

    Args:
        nivel: Nível de logging (default: INFO).

    Returns:
        Logger configurado com formato JSON.
    """
    logger = logging.getLogger("viagem_inteligente")
    logger.setLevel(nivel)

    # Remover handlers existentes para evitar duplicação
    logger.handlers.clear()

    # Handler para console com JSON
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

    # Handler para arquivo de logs (rotativo)
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "agent.log")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    return logger


# Logger global da aplicação
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Retorna o logger estruturado da aplicação (singleton)."""
    global _logger
    if _logger is None:
        _logger = configurar_logging_estruturado()
    return _logger


# ---------------------------------------------------------------------------
# Sinal 2: Registro de Auditoria (Trace)
# ---------------------------------------------------------------------------

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_DB_PATH = os.path.join(_DB_DIR, "observabilidade.db")
_db_lock = threading.Lock()


def _get_db() -> sqlite3.Connection:
    """Obtém conexão com o banco de auditoria."""
    os.makedirs(_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            node TEXT NOT NULL,
            status TEXT NOT NULL,
            latency_ms REAL,
            input_summary TEXT,
            output_summary TEXT,
            error TEXT,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_traces_trace_id ON traces(trace_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(timestamp)
    """)
    conn.commit()
    return conn


class Trace:
    """Representa um trace completo de uma execução do agente.

    Correlaciona logs estruturados com registros de auditoria
    através do trace_id único.
    """

    def __init__(self, trace_id: Optional[str] = None):
        """Inicia um novo trace.

        Args:
            trace_id: ID único do trace. Se None, gera um UUID.
        """
        self.trace_id = trace_id or str(uuid.uuid4())[:8]
        self.start_time = time.time()
        self.nodes: list[dict] = []
        self._logger = get_logger()

    @contextmanager
    def span(self, node_name: str, input_summary: str = ""):
        """Context manager para medir a execução de um nó.

        Args:
            node_name: Nome do nó sendo executado.
            input_summary: Resumo dos dados de entrada (para auditoria).

        Yields:
            Dict para armazenar dados de saída do span.

        Example:
            with trace.span("consulta_voo", "codigo=ABC123") as span_data:
                resultado = consultar_voo(...)
                span_data["output"] = "Voo LA3456 cancelado"
        """
        span_data = {"output": "", "error": None, "metadata": {}}
        node_start = time.time()

        self._logger.info(
            "Node iniciado",
            extra={
                "trace_id": self.trace_id,
                "node": node_name,
                "status_code": "STARTED",
            }
        )

        try:
            yield span_data
            latency_ms = (time.time() - node_start) * 1000
            status = "OK"

            self._logger.info(
                "Node concluído",
                extra={
                    "trace_id": self.trace_id,
                    "node": node_name,
                    "latency_ms": round(latency_ms, 2),
                    "status_code": "OK",
                }
            )

        except Exception as e:
            latency_ms = (time.time() - node_start) * 1000
            status = "ERROR"
            span_data["error"] = str(e)

            self._logger.error(
                f"Node falhou: {e}",
                extra={
                    "trace_id": self.trace_id,
                    "node": node_name,
                    "latency_ms": round(latency_ms, 2),
                    "status_code": "ERROR",
                    "error_type": type(e).__name__,
                }
            )
            raise

        finally:
            # Registrar no banco de auditoria (sinal 2)
            record = {
                "trace_id": self.trace_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": node_name,
                "status": status,
                "latency_ms": round(latency_ms, 2),
                "input_summary": input_summary[:500] if input_summary else "",
                "output_summary": str(span_data.get("output", ""))[:500],
                "error": span_data.get("error"),
                "metadata": json.dumps(span_data.get("metadata", {})),
            }
            self.nodes.append(record)
            self._persist_record(record)

    def finalizar(self) -> dict:
        """Finaliza o trace e retorna um resumo da execução.

        Returns:
            Dict com resumo da execução completa.
        """
        total_ms = (time.time() - self.start_time) * 1000
        erros = [n for n in self.nodes if n["status"] == "ERROR"]

        resumo = {
            "trace_id": self.trace_id,
            "total_latency_ms": round(total_ms, 2),
            "total_nodes": len(self.nodes),
            "nodes_ok": len(self.nodes) - len(erros),
            "nodes_error": len(erros),
            "nodes": [
                {
                    "node": n["node"],
                    "status": n["status"],
                    "latency_ms": n["latency_ms"],
                }
                for n in self.nodes
            ],
        }

        self._logger.info(
            "Trace finalizado",
            extra={
                "trace_id": self.trace_id,
                "latency_ms": round(total_ms, 2),
                "status_code": "COMPLETED" if not erros else "PARTIAL_ERROR",
            }
        )

        return resumo

    def _persist_record(self, record: dict):
        """Persiste um registro de span no banco de auditoria."""
        try:
            with _db_lock:
                conn = _get_db()
                conn.execute(
                    """INSERT INTO traces
                    (trace_id, timestamp, node, status, latency_ms,
                     input_summary, output_summary, error, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record["trace_id"],
                        record["timestamp"],
                        record["node"],
                        record["status"],
                        record["latency_ms"],
                        record["input_summary"],
                        record["output_summary"],
                        record["error"],
                        record["metadata"],
                    ),
                )
                conn.commit()
                conn.close()
        except Exception as e:
            self._logger.warning(f"Falha ao persistir trace: {e}")


# ---------------------------------------------------------------------------
# Funções de consulta (investigação de execuções)
# ---------------------------------------------------------------------------


def consultar_trace(trace_id: str) -> list[dict]:
    """Consulta todos os registros de um trace para investigação.

    Args:
        trace_id: ID do trace a investigar.

    Returns:
        Lista de registros ordenados cronologicamente.
    """
    try:
        with _db_lock:
            conn = _get_db()
            cursor = conn.execute(
                "SELECT * FROM traces WHERE trace_id = ? ORDER BY timestamp",
                (trace_id,),
            )
            colunas = [desc[0] for desc in cursor.description]
            registros = [dict(zip(colunas, row)) for row in cursor.fetchall()]
            conn.close()
            return registros
    except Exception:
        return []


def consultar_traces_recentes(limite: int = 10) -> list[dict]:
    """Consulta os traces mais recentes.

    Args:
        limite: Número máximo de traces a retornar.

    Returns:
        Lista de resumos dos traces mais recentes.
    """
    try:
        with _db_lock:
            conn = _get_db()
            cursor = conn.execute(
                """SELECT trace_id,
                          MIN(timestamp) as inicio,
                          MAX(timestamp) as fim,
                          COUNT(*) as total_nodes,
                          SUM(CASE WHEN status='ERROR' THEN 1 ELSE 0 END) as erros,
                          SUM(latency_ms) as total_latency_ms
                   FROM traces
                   GROUP BY trace_id
                   ORDER BY inicio DESC
                   LIMIT ?""",
                (limite,),
            )
            resultados = []
            for row in cursor.fetchall():
                resultados.append({
                    "trace_id": row[0],
                    "inicio": row[1],
                    "fim": row[2],
                    "total_nodes": row[3],
                    "erros": row[4],
                    "total_latency_ms": round(row[5], 2) if row[5] else 0,
                })
            conn.close()
            return resultados
    except Exception:
        return []


def detectar_anomalias(janela_minutos: int = 60) -> list[dict]:
    """Detecta anomalias nas execuções recentes.

    Identifica:
    - Latência acima do percentil 95
    - Taxa de erro acima de 20%
    - Nós com falhas recorrentes

    Args:
        janela_minutos: Janela de tempo para análise (em minutos).

    Returns:
        Lista de anomalias detectadas.
    """
    anomalias = []

    try:
        with _db_lock:
            conn = _get_db()

            # 1. Verificar latência alta por nó
            cursor = conn.execute(
                """SELECT node, AVG(latency_ms) as avg_ms, MAX(latency_ms) as max_ms,
                          COUNT(*) as execucoes
                   FROM traces
                   WHERE timestamp > datetime('now', ?)
                   GROUP BY node""",
                (f"-{janela_minutos} minutes",),
            )
            for row in cursor.fetchall():
                node, avg_ms, max_ms, execucoes = row
                # Anomalia: latência máxima > 3x a média
                if avg_ms and max_ms > avg_ms * 3 and max_ms > 1000:
                    anomalias.append({
                        "tipo": "latencia_alta",
                        "node": node,
                        "avg_ms": round(avg_ms, 2),
                        "max_ms": round(max_ms, 2),
                        "execucoes": execucoes,
                        "descricao": (
                            f"Nó '{node}' com latência máxima ({max_ms:.0f}ms) "
                            f"3x acima da média ({avg_ms:.0f}ms)"
                        ),
                    })

            # 2. Verificar taxa de erro por nó
            cursor = conn.execute(
                """SELECT node,
                          COUNT(*) as total,
                          SUM(CASE WHEN status='ERROR' THEN 1 ELSE 0 END) as erros
                   FROM traces
                   WHERE timestamp > datetime('now', ?)
                   GROUP BY node
                   HAVING total >= 3""",
                (f"-{janela_minutos} minutes",),
            )
            for row in cursor.fetchall():
                node, total, erros = row
                taxa_erro = erros / total if total > 0 else 0
                if taxa_erro > 0.2:
                    anomalias.append({
                        "tipo": "taxa_erro_alta",
                        "node": node,
                        "total": total,
                        "erros": erros,
                        "taxa": round(taxa_erro * 100, 1),
                        "descricao": (
                            f"Nó '{node}' com taxa de erro de {taxa_erro*100:.1f}% "
                            f"({erros}/{total} execuções)"
                        ),
                    })

            conn.close()

    except Exception as e:
        anomalias.append({
            "tipo": "erro_analise",
            "descricao": f"Falha ao analisar anomalias: {e}",
        })

    return anomalias


def gerar_relatorio_observabilidade(trace_id: Optional[str] = None) -> str:
    """Gera um relatório de observabilidade em Markdown.

    Args:
        trace_id: Se informado, gera relatório de um trace específico.
                  Se None, gera relatório geral dos traces recentes.

    Returns:
        Relatório em formato Markdown.
    """
    if trace_id:
        registros = consultar_trace(trace_id)
        if not registros:
            return f"Nenhum registro encontrado para trace_id={trace_id}"

        total_ms = sum(r.get("latency_ms", 0) for r in registros)
        erros = [r for r in registros if r["status"] == "ERROR"]

        relatorio = f"## Relatório de Execução — Trace {trace_id}\n\n"
        relatorio += "| Métrica | Valor |\n|---------|-------|\n"
        relatorio += f"| Trace ID | `{trace_id}` |\n"
        relatorio += f"| Total de Nós | {len(registros)} |\n"
        relatorio += f"| Latência Total | {total_ms:.0f}ms |\n"
        relatorio += f"| Erros | {len(erros)} |\n\n"

        relatorio += "### Detalhamento por Nó\n\n"
        relatorio += "| # | Nó | Status | Latência | Erro |\n"
        relatorio += "|---|-----|--------|----------|------|\n"
        for i, r in enumerate(registros, 1):
            erro_txt = r.get("error", "-") or "-"
            relatorio += (
                f"| {i} | {r['node']} | {r['status']} | "
                f"{r.get('latency_ms', 0):.0f}ms | {erro_txt} |\n"
            )

        return relatorio

    # Relatório geral
    recentes = consultar_traces_recentes(20)
    anomalias = detectar_anomalias()

    relatorio = "## Relatório de Observabilidade\n\n"
    relatorio += f"### Últimas {len(recentes)} Execuções\n\n"
    relatorio += "| Trace ID | Início | Nós | Erros | Latência |\n"
    relatorio += "|----------|--------|-----|-------|----------|\n"
    for t in recentes:
        relatorio += (
            f"| `{t['trace_id']}` | {t['inicio'][:19]} | "
            f"{t['total_nodes']} | {t['erros']} | {t['total_latency_ms']:.0f}ms |\n"
        )

    if anomalias:
        relatorio += "\n### Anomalias Detectadas\n\n"
        for a in anomalias:
            relatorio += f"- **{a['tipo']}**: {a['descricao']}\n"

    return relatorio
