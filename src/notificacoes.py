"""
Sistema de notificações proativas para mudanças de status de voo.

v2.0: Monitora voos registrados e envia notificações quando há
alterações (cancelamento, atraso, mudança de gate, etc.).
"""

import logging
import threading
import time
from datetime import datetime
from typing import Callable, Optional

from src.persistencia import get_gerenciador

logger = logging.getLogger(__name__)


class Notificacao:
    """Representa uma notificação a ser enviada ao usuário."""

    def __init__(self, tipo: str, titulo: str, mensagem: str,
                 thread_id: str = "", dados: Optional[dict] = None):
        self.tipo = tipo  # "status_voo", "clima_adverso", "lembrete"
        self.titulo = titulo
        self.mensagem = mensagem
        self.thread_id = thread_id
        self.dados = dados or {}
        self.timestamp = datetime.now().isoformat()
        self.lida = False

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "titulo": self.titulo,
            "mensagem": self.mensagem,
            "thread_id": self.thread_id,
            "dados": self.dados,
            "timestamp": self.timestamp,
            "lida": self.lida,
        }


class FilaNotificacoes:
    """Fila thread-safe para acumular notificações pendentes."""

    def __init__(self):
        self._fila: list[Notificacao] = []
        self._lock = threading.Lock()
        self._callbacks: list[Callable] = []

    def adicionar(self, notificacao: Notificacao):
        """Adiciona notificação à fila e dispara callbacks."""
        with self._lock:
            self._fila.append(notificacao)
            logger.info("Notificação adicionada: %s", notificacao.titulo)

        # Disparar callbacks registrados
        for callback in self._callbacks:
            try:
                callback(notificacao)
            except Exception as e:
                logger.warning("Erro ao disparar callback de notificação: %s", e)

    def obter_pendentes(self, thread_id: Optional[str] = None) -> list[dict]:
        """Obtém notificações pendentes (não lidas).

        Args:
            thread_id: Filtrar por sessão específica. None retorna todas.

        Returns:
            Lista de notificações não lidas.
        """
        with self._lock:
            pendentes = [
                n for n in self._fila
                if not n.lida and (thread_id is None or n.thread_id == thread_id)
            ]
            return [n.to_dict() for n in pendentes]

    def marcar_lidas(self, thread_id: Optional[str] = None):
        """Marca notificações como lidas."""
        with self._lock:
            for n in self._fila:
                if thread_id is None or n.thread_id == thread_id:
                    n.lida = True

    def registrar_callback(self, callback: Callable):
        """Registra callback para ser chamado quando nova notificação chegar.

        Args:
            callback: Função que recebe uma Notificacao como argumento.
        """
        self._callbacks.append(callback)

    def limpar(self):
        """Remove notificações já lidas."""
        with self._lock:
            self._fila = [n for n in self._fila if not n.lida]


class MonitorVoos:
    """Monitora voos registrados e gera notificações proativas.

    Verifica periodicamente se houve mudança no status dos voos
    associados a sessões ativas.
    """

    def __init__(self, fila: FilaNotificacoes, intervalo_segundos: int = 300):
        """Inicializa o monitor.

        Args:
            fila: Fila de notificações para enviar alertas.
            intervalo_segundos: Intervalo entre verificações (default: 5 min).
        """
        self.fila = fila
        self.intervalo = intervalo_segundos
        self._thread: Optional[threading.Thread] = None
        self._rodando = False
        self._status_anterior: dict[str, str] = {}

    def iniciar(self):
        """Inicia o monitoramento em background."""
        if self._rodando:
            return

        self._rodando = True
        self._thread = threading.Thread(target=self._loop_monitoramento, daemon=True)
        self._thread.start()
        logger.info("Monitor de voos iniciado (intervalo: %ds)", self.intervalo)

    def parar(self):
        """Para o monitoramento."""
        self._rodando = False
        if self._thread:
            self._thread.join(timeout=5)
            logger.info("Monitor de voos encerrado")

    def _loop_monitoramento(self):
        """Loop principal de monitoramento."""
        while self._rodando:
            try:
                self._verificar_mudancas()
            except Exception as e:
                logger.error("Erro no monitoramento de voos: %s", e)
            time.sleep(self.intervalo)

    def _verificar_mudancas(self):
        """Verifica mudanças de status em voos monitorados."""
        from src.ferramentas.voo import VOOS_DB

        gerenciador = get_gerenciador()
        sessoes = gerenciador.listar_sessoes()

        for sessao in sessoes:
            codigo = sessao.get("codigo_reserva", "")
            if not codigo:
                continue

            voo = VOOS_DB.get(codigo)
            if not voo:
                continue

            status_atual = voo.get("status", "")
            status_ant = self._status_anterior.get(codigo, "")

            # Detectar mudança de status
            if status_ant and status_atual != status_ant:
                self._gerar_notificacao_mudanca(
                    codigo=codigo,
                    status_anterior=status_ant,
                    status_novo=status_atual,
                    voo=voo,
                    thread_id=sessao.get("thread_id", ""),
                )

            self._status_anterior[codigo] = status_atual

    def _gerar_notificacao_mudanca(self, codigo: str, status_anterior: str,
                                    status_novo: str, voo: dict, thread_id: str):
        """Gera notificação para mudança de status de voo."""
        mensagens_status = {
            "cancelado": "⚠️ Seu voo foi CANCELADO",
            "atrasado": "⏰ Seu voo sofreu um ATRASO",
            "embarcando": "🛫 Seu voo está EMBARCANDO",
            "confirmado": "✅ Seu voo foi CONFIRMADO",
        }

        titulo = mensagens_status.get(
            status_novo, f"Mudança de status: {status_novo}"
        )

        mensagem = (
            f"Voo {voo.get('numero_voo', 'N/A')} ({voo.get('origem', '')} → "
            f"{voo.get('destino', '')})\n"
            f"Status anterior: {status_anterior}\n"
            f"Novo status: {status_novo}\n"
        )

        if voo.get("motivo") and voo["motivo"] != "N/A":
            mensagem += f"Motivo: {voo['motivo']}\n"

        notificacao = Notificacao(
            tipo="status_voo",
            titulo=titulo,
            mensagem=mensagem,
            thread_id=thread_id,
            dados={
                "codigo_reserva": codigo,
                "numero_voo": voo.get("numero_voo", ""),
                "status_anterior": status_anterior,
                "status_novo": status_novo,
            },
        )

        self.fila.adicionar(notificacao)

        # Registrar evento no analytics
        gerenciador = get_gerenciador()
        gerenciador.registrar_evento_analytics(
            evento="notificacao_proativa",
            thread_id=thread_id,
            dados=notificacao.to_dict(),
        )


# Instâncias globais
_fila_notificacoes: Optional[FilaNotificacoes] = None
_monitor_voos: Optional[MonitorVoos] = None


def get_fila_notificacoes() -> FilaNotificacoes:
    """Retorna instância singleton da fila de notificações."""
    global _fila_notificacoes
    if _fila_notificacoes is None:
        _fila_notificacoes = FilaNotificacoes()
    return _fila_notificacoes


def get_monitor_voos() -> MonitorVoos:
    """Retorna instância singleton do monitor de voos."""
    global _monitor_voos
    if _monitor_voos is None:
        _monitor_voos = MonitorVoos(get_fila_notificacoes())
    return _monitor_voos


def iniciar_monitoramento():
    """Inicia o sistema de monitoramento proativo."""
    monitor = get_monitor_voos()
    monitor.iniciar()
    return monitor
