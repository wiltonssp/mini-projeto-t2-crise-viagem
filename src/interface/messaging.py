"""
Adaptadores de integração com plataformas de mensageria.

v2.0: Suporte a WhatsApp (via Twilio) e Telegram (via python-telegram-bot).
Implementa padrão adapter para facilitar adição de novos canais.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class MensageriaAdapter(ABC):
    """Interface abstrata para adaptadores de mensageria."""

    @abstractmethod
    def enviar_mensagem(self, destinatario: str, mensagem: str) -> bool:
        """Envia mensagem para o destinatario.

        Args:
            destinatario: Identificador do destinatário (telefone, chat_id).
            mensagem: Texto a enviar.

        Returns:
            True se enviou com sucesso.
        """
        ...

    @abstractmethod
    def processar_webhook(self, payload: dict) -> Optional[dict]:
        """Processa payload recebido via webhook.

        Args:
            payload: Dados do webhook da plataforma.

        Returns:
            Dict com 'remetente' e 'mensagem' ou None se inválido.
        """
        ...

    @abstractmethod
    def nome(self) -> str:
        """Nome do canal de mensageria."""
        ...


class WhatsAppAdapter(MensageriaAdapter):
    """Adaptador para WhatsApp via Twilio API.

    Requer variáveis de ambiente:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_WHATSAPP_NUMBER (formato: whatsapp:+14155238886)
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.numero_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
        self._client = None

    @property
    def disponivel(self) -> bool:
        """Verifica se as credenciais estão configuradas."""
        return bool(self.account_sid and self.auth_token and self.numero_whatsapp)

    def _get_client(self):
        """Obtém cliente Twilio (lazy load)."""
        if self._client is None and self.disponivel:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.warning("Pacote 'twilio' não instalado. pip install twilio")
                return None
        return self._client

    def enviar_mensagem(self, destinatario: str, mensagem: str) -> bool:
        """Envia mensagem via WhatsApp (Twilio).

        Args:
            destinatario: Número no formato 'whatsapp:+5511999999999'.
            mensagem: Texto a enviar (max 1600 chars por mensagem).
        """
        client = self._get_client()
        if not client:
            logger.warning("WhatsApp: cliente Twilio não disponível")
            return False

        try:
            # Dividir mensagem longa em partes (limite WhatsApp: 1600 chars)
            partes = self._dividir_mensagem(mensagem, max_chars=1600)

            for parte in partes:
                client.messages.create(
                    body=parte,
                    from_=self.numero_whatsapp,
                    to=destinatario,
                )

            logger.info("WhatsApp: mensagem enviada para %s", destinatario)
            return True
        except Exception as e:
            logger.error("WhatsApp: erro ao enviar mensagem: %s", e)
            return False

    def processar_webhook(self, payload: dict) -> Optional[dict]:
        """Processa webhook do Twilio (WhatsApp incoming)."""
        try:
            remetente = payload.get("From", "")
            mensagem = payload.get("Body", "")

            if not remetente or not mensagem:
                return None

            return {
                "remetente": remetente,
                "mensagem": mensagem,
                "canal": self.nome(),
                "metadata": {
                    "message_sid": payload.get("MessageSid", ""),
                    "num_media": payload.get("NumMedia", "0"),
                },
            }
        except Exception as e:
            logger.error("WhatsApp: erro ao processar webhook: %s", e)
            return None

    def _dividir_mensagem(self, texto: str, max_chars: int = 1600) -> list[str]:
        """Divide mensagem longa em partes respeitando limite de caracteres."""
        if len(texto) <= max_chars:
            return [texto]

        partes = []
        while texto:
            if len(texto) <= max_chars:
                partes.append(texto)
                break
            # Encontrar ponto de quebra (parágrafo ou espaço)
            ponto_quebra = texto.rfind("\n\n", 0, max_chars)
            if ponto_quebra == -1:
                ponto_quebra = texto.rfind("\n", 0, max_chars)
            if ponto_quebra == -1:
                ponto_quebra = texto.rfind(" ", 0, max_chars)
            if ponto_quebra == -1:
                ponto_quebra = max_chars

            partes.append(texto[:ponto_quebra])
            texto = texto[ponto_quebra:].lstrip()

        return partes

    def nome(self) -> str:
        return "whatsapp"


class TelegramAdapter(MensageriaAdapter):
    """Adaptador para Telegram via Bot API.

    Requer variável de ambiente:
    - TELEGRAM_BOT_TOKEN
    """

    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    @property
    def disponivel(self) -> bool:
        """Verifica se o token do bot está configurado."""
        return bool(self.bot_token)

    def enviar_mensagem(self, destinatario: str, mensagem: str) -> bool:
        """Envia mensagem via Telegram Bot API.

        Args:
            destinatario: chat_id do Telegram.
            mensagem: Texto a enviar (suporta Markdown).
        """
        if not self.disponivel:
            logger.warning("Telegram: bot token não configurado")
            return False

        try:
            import requests
            url = f"{self.BASE_URL}{self.bot_token}/sendMessage"

            # Dividir mensagem se necessário (limite Telegram: 4096 chars)
            partes = self._dividir_mensagem(mensagem, max_chars=4096)

            for parte in partes:
                resp = requests.post(url, json={
                    "chat_id": destinatario,
                    "text": parte,
                    "parse_mode": "Markdown",
                }, timeout=10)

                if not resp.ok:
                    # Tentar sem Markdown se falhar
                    resp = requests.post(url, json={
                        "chat_id": destinatario,
                        "text": parte,
                    }, timeout=10)

            logger.info("Telegram: mensagem enviada para %s", destinatario)
            return True
        except Exception as e:
            logger.error("Telegram: erro ao enviar mensagem: %s", e)
            return False

    def processar_webhook(self, payload: dict) -> Optional[dict]:
        """Processa webhook do Telegram (update)."""
        try:
            message = payload.get("message", {})
            if not message:
                return None

            chat = message.get("chat", {})
            texto = message.get("text", "")

            if not texto:
                return None

            return {
                "remetente": str(chat.get("id", "")),
                "mensagem": texto,
                "canal": self.nome(),
                "metadata": {
                    "chat_type": chat.get("type", "private"),
                    "username": message.get("from", {}).get("username", ""),
                    "first_name": message.get("from", {}).get("first_name", ""),
                    "message_id": message.get("message_id", ""),
                },
            }
        except Exception as e:
            logger.error("Telegram: erro ao processar webhook: %s", e)
            return None

    def _dividir_mensagem(self, texto: str, max_chars: int = 4096) -> list[str]:
        """Divide mensagem longa respeitando limite do Telegram."""
        if len(texto) <= max_chars:
            return [texto]

        partes = []
        while texto:
            if len(texto) <= max_chars:
                partes.append(texto)
                break
            ponto_quebra = texto.rfind("\n\n", 0, max_chars)
            if ponto_quebra == -1:
                ponto_quebra = texto.rfind("\n", 0, max_chars)
            if ponto_quebra == -1:
                ponto_quebra = max_chars
            partes.append(texto[:ponto_quebra])
            texto = texto[ponto_quebra:].lstrip()

        return partes

    def nome(self) -> str:
        return "telegram"


class ServicoMensageria:
    """Serviço centralizado de mensageria multi-canal.

    Gerencia todos os adaptadores de mensageria disponíveis e
    roteia mensagens para o canal correto.
    """

    def __init__(self):
        self._adapters: dict[str, MensageriaAdapter] = {}
        self._inicializar_adapters()

    def _inicializar_adapters(self):
        """Inicializa adaptadores disponíveis."""
        whatsapp = WhatsAppAdapter()
        if whatsapp.disponivel:
            self._adapters["whatsapp"] = whatsapp
            logger.info("WhatsApp adapter ativado")

        telegram = TelegramAdapter()
        if telegram.disponivel:
            self._adapters["telegram"] = telegram
            logger.info("Telegram adapter ativado")

    @property
    def canais_disponiveis(self) -> list[str]:
        """Lista canais de mensageria disponíveis."""
        return list(self._adapters.keys())

    def enviar(self, canal: str, destinatario: str, mensagem: str) -> bool:
        """Envia mensagem pelo canal especificado.

        Args:
            canal: Nome do canal ('whatsapp', 'telegram').
            destinatario: ID do destinatário.
            mensagem: Texto a enviar.

        Returns:
            True se enviou com sucesso.
        """
        adapter = self._adapters.get(canal)
        if not adapter:
            logger.warning("Canal '%s' não disponível", canal)
            return False
        return adapter.enviar_mensagem(destinatario, mensagem)

    def processar_incoming(self, canal: str, payload: dict) -> Optional[dict]:
        """Processa mensagem recebida de um canal.

        Args:
            canal: Nome do canal de origem.
            payload: Dados do webhook.

        Returns:
            Dict com remetente e mensagem processada.
        """
        adapter = self._adapters.get(canal)
        if not adapter:
            return None
        return adapter.processar_webhook(payload)

    def processar_e_responder(self, canal: str, payload: dict) -> Optional[str]:
        """Processa mensagem incoming e gera resposta via agente.

        Integra o fluxo completo: recebe mensagem → processa no agente → responde.

        Args:
            canal: Canal de origem.
            payload: Dados do webhook.

        Returns:
            Resposta gerada ou None se falhou.
        """
        dados = self.processar_incoming(canal, payload)
        if not dados:
            return None

        remetente = dados["remetente"]
        mensagem = dados["mensagem"]

        try:
            from src.agente import build_graph

            graph = build_graph()
            thread_id = f"{canal}-{remetente}"
            config = {"configurable": {"thread_id": thread_id}}

            resultado = graph.invoke(
                {"messages": [HumanMessage(content=mensagem)]},
                config,
            )

            resposta = resultado.get("relatorio_final", "")
            if not resposta:
                mensagens = resultado.get("messages", [])
                if mensagens:
                    ultima = mensagens[-1]
                    resposta = ultima.content if hasattr(ultima, "content") else ""

            if resposta:
                # Enviar resposta de volta pelo mesmo canal
                self.enviar(canal, remetente, resposta)
                return resposta

        except Exception as e:
            logger.error("Erro ao processar mensagem %s de %s: %s",
                         canal, remetente, e)

        return None


# Instância singleton
_servico: Optional[ServicoMensageria] = None


def get_servico_mensageria() -> ServicoMensageria:
    """Retorna instância singleton do serviço de mensageria."""
    global _servico
    if _servico is None:
        _servico = ServicoMensageria()
    return _servico
