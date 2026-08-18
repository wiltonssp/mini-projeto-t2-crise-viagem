"""
Endpoint webhook para integração low-code/no-code.

Expõe endpoints HTTP simples que permitem ferramentas como n8n, Make.com
ou Zapier interagir com o agente de gestão de crises.

Endpoints:
- POST /webhook/alerta-voo: Recebe alerta de voo cancelado/atrasado
  e retorna o plano de contingência gerado pelo agente.
- GET /webhook/health: Health check para monitoramento.
- GET /webhook/metricas: Retorna métricas de observabilidade.
"""

import json
import logging
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Optional

from langchain_core.messages import HumanMessage

from src.observabilidade import Trace, get_logger

logger = logging.getLogger(__name__)

# Porta padrão do webhook
WEBHOOK_PORT = 5000

# Instância do grafo (lazy-loaded)
_graph = None


def _get_graph():
    """Retorna o grafo compilado para uso no webhook."""
    global _graph
    if _graph is None:
        from src.agente import build_graph
        _graph = build_graph()
    return _graph


class WebhookHandler(BaseHTTPRequestHandler):
    """Handler HTTP para receber webhooks de ferramentas low-code."""

    def do_GET(self):
        """Health check e métricas."""
        if self.path == "/webhook/health":
            self._responder_json(200, {
                "status": "healthy",
                "service": "viagem-inteligente",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
        elif self.path == "/webhook/metricas":
            from src.observabilidade import consultar_traces_recentes, detectar_anomalias
            traces = consultar_traces_recentes(10)
            anomalias = detectar_anomalias(60)
            self._responder_json(200, {
                "traces_recentes": len(traces),
                "anomalias": len(anomalias),
                "detalhes_anomalias": anomalias,
                "ultimos_traces": traces[:5],
            })
        else:
            self._responder_json(404, {"erro": "Endpoint não encontrado"})

    def do_POST(self):
        """Recebe alertas de voo e processa com o agente."""
        if self.path == "/webhook/alerta-voo":
            self._processar_alerta_voo()
        else:
            self._responder_json(404, {"erro": "Endpoint não encontrado"})

    def _processar_alerta_voo(self):
        """Processa alerta de voo cancelado/atrasado.

        Payload esperado (JSON):
        {
            "codigo_reserva": "ABC123",
            "mensagem": "Voo cancelado por mau tempo",
            "canal_resposta": "discord" | "email" | "log"  (opcional)
        }
        """
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            dados = json.loads(body)

            codigo = dados.get("codigo_reserva", "")
            mensagem = dados.get("mensagem", "")
            canal = dados.get("canal_resposta", "log")

            if not codigo or not mensagem:
                self._responder_json(400, {
                    "erro": "Campos 'codigo_reserva' e 'mensagem' são obrigatórios",
                    "exemplo": {
                        "codigo_reserva": "ABC123",
                        "mensagem": "Meu voo foi cancelado",
                        "canal_resposta": "log"
                    }
                })
                return

            # Processar com o agente
            obs_logger = get_logger()
            trace = Trace()

            with trace.span("webhook_alerta_voo", f"codigo={codigo}") as span_data:
                graph = _get_graph()
                config = {"configurable": {"thread_id": f"webhook-{codigo}-{int(time.time())}"}}

                resultado = graph.invoke(
                    {"messages": [HumanMessage(content=f"{codigo} {mensagem}")]},
                    config,
                )

                relatorio = resultado.get("relatorio_final", "Sem relatório gerado.")
                span_data["output"] = f"relatorio_length={len(relatorio)}"
                span_data["metadata"] = {"canal": canal, "codigo": codigo}

            trace_resumo = trace.finalizar()

            # Registrar saída observável
            obs_logger.info(
                f"Webhook processado: codigo={codigo} canal={canal}",
                extra={
                    "trace_id": trace.trace_id,
                    "node": "webhook",
                    "latency_ms": trace_resumo["total_latency_ms"],
                }
            )

            resposta = {
                "status": "processado",
                "trace_id": trace.trace_id,
                "codigo_reserva": codigo,
                "canal_resposta": canal,
                "plano_contingencia": relatorio,
                "latency_ms": trace_resumo["total_latency_ms"],
            }

            self._responder_json(200, resposta)

        except json.JSONDecodeError:
            self._responder_json(400, {"erro": "Payload JSON inválido"})
        except Exception as e:
            logger.error(f"Erro no webhook: {e}")
            self._responder_json(500, {"erro": f"Erro interno: {str(e)[:200]}"})

    def _responder_json(self, status: int, dados: dict):
        """Envia resposta JSON."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        """Suprime logs padrão do HTTPServer (usamos logging estruturado)."""
        logger.debug(f"Webhook: {args[0]}")


def iniciar_webhook(port: int = WEBHOOK_PORT, background: bool = False) -> Optional[HTTPServer]:
    """Inicia o servidor webhook.

    Args:
        port: Porta do servidor (default: 5000).
        background: Se True, roda em thread separada.

    Returns:
        Instância do HTTPServer se background=True.
    """
    server = HTTPServer(("127.0.0.1", port), WebhookHandler)
    logger.info(f"Webhook iniciado em http://127.0.0.1:{port}")
    print(f"🔗 Webhook ativo em http://127.0.0.1:{port}/webhook/alerta-voo")

    if background:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server
    else:
        server.serve_forever()
        return None
