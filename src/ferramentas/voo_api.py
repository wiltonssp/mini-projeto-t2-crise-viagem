"""
Camada de integração com APIs reais de aviação.

Implementa o padrão adapter para integração com APIs de aviação reais
(FlightAware, Amadeus, Cirium) com fallback para a base simulada.

v2.0: Suporte a múltiplos providers com fallback gracioso.
"""

import os
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

import requests

from src.ferramentas.voo import VOOS_DB, _gerar_voos_db

logger = logging.getLogger(__name__)


class AviationProvider(ABC):
    """Interface abstrata para provedores de dados de aviação."""

    @abstractmethod
    def consultar_voo(self, codigo_reserva: str) -> Optional[dict]:
        """Consulta status de um voo pelo código de reserva.

        Args:
            codigo_reserva: Código alfanumérico da reserva.

        Returns:
            Dict com dados do voo ou None se não encontrado/indisponível.
        """
        ...

    @abstractmethod
    def buscar_por_numero_voo(self, numero_voo: str,
                              data: Optional[str] = None) -> Optional[dict]:
        """Consulta status por número de voo (ex: LA3456).

        Args:
            numero_voo: Código IATA do voo.
            data: Data no formato YYYY-MM-DD (default: hoje).

        Returns:
            Dict com dados do voo ou None se não encontrado.
        """
        ...

    @abstractmethod
    def nome(self) -> str:
        """Nome do provedor para logs e identificação."""
        ...


class SimulatedProvider(AviationProvider):
    """Provedor simulado usando a base de dados local (MVP/desenvolvimento).

    Usa a mesma VOOS_DB já existente no projeto, garantindo compatibilidade
    retroativa com o comportamento v1.0.
    """

    def consultar_voo(self, codigo_reserva: str) -> Optional[dict]:
        """Consulta na base simulada VOOS_DB."""
        voo = VOOS_DB.get(codigo_reserva.upper())
        if voo:
            return {
                "numero_voo": voo["numero_voo"],
                "origem": voo["origem"],
                "destino": voo["destino"],
                "horario_partida": voo["horario_partida"],
                "horario_chegada": voo["horario_chegada"],
                "status": voo["status"],
                "motivo": voo["motivo"],
                "provider": self.nome(),
            }
        return None

    def buscar_por_numero_voo(self, numero_voo: str,
                              data: Optional[str] = None) -> Optional[dict]:
        """Busca na base simulada por número de voo."""
        for _codigo, voo in VOOS_DB.items():
            if voo["numero_voo"].replace(" ", "") == numero_voo.replace(" ", ""):
                return {
                    "numero_voo": voo["numero_voo"],
                    "origem": voo["origem"],
                    "destino": voo["destino"],
                    "horario_partida": voo["horario_partida"],
                    "horario_chegada": voo["horario_chegada"],
                    "status": voo["status"],
                    "motivo": voo["motivo"],
                    "provider": self.nome(),
                }
        return None

    def nome(self) -> str:
        return "simulado"


class FlightAwareProvider(AviationProvider):
    """Provedor FlightAware AeroAPI para dados reais de voo.

    Requer variável de ambiente FLIGHTAWARE_API_KEY.
    Documentação: https://www.flightaware.com/aeroapi/
    """

    BASE_URL = "https://aeroapi.flightaware.com/aeroapi"

    def __init__(self):
        self.api_key = os.getenv("FLIGHTAWARE_API_KEY", "")
        self._timeout = 15

    def _headers(self) -> dict:
        return {
            "x-apikey": self.api_key,
            "Accept": "application/json",
        }

    def _disponivel(self) -> bool:
        """Verifica se a API key está configurada."""
        return bool(self.api_key and self.api_key.strip())

    def consultar_voo(self, codigo_reserva: str) -> Optional[dict]:
        """FlightAware não suporta consulta por código de reserva diretamente.

        Retorna None para fallback ao provider simulado.
        """
        return None

    def buscar_por_numero_voo(self, numero_voo: str,
                              data: Optional[str] = None) -> Optional[dict]:
        """Consulta status do voo via FlightAware AeroAPI."""
        if not self._disponivel():
            return None

        try:
            # Formatar identificador do voo (remover espaços)
            voo_id = numero_voo.replace(" ", "")
            url = f"{self.BASE_URL}/flights/{voo_id}"

            resp = requests.get(url, headers=self._headers(), timeout=self._timeout)
            resp.raise_for_status()
            data_resp = resp.json()

            flights = data_resp.get("flights", [])
            if not flights:
                return None

            # Pegar o voo mais recente
            voo = flights[0]
            return {
                "numero_voo": numero_voo,
                "origem": voo.get("origin", {}).get("code_iata", "N/A"),
                "destino": voo.get("destination", {}).get("code_iata", "N/A"),
                "horario_partida": voo.get("scheduled_out", "N/A"),
                "horario_chegada": voo.get("scheduled_in", "N/A"),
                "status": self._mapear_status(voo.get("status", "")),
                "motivo": voo.get("cancellation_reason", "N/A"),
                "provider": self.nome(),
            }
        except requests.exceptions.Timeout:
            logger.warning("FlightAware API timeout para voo %s", numero_voo)
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning("FlightAware API erro HTTP: %s", e)
            return None
        except Exception as e:
            logger.warning("FlightAware erro inesperado: %s", e)
            return None

    def _mapear_status(self, status_raw: str) -> str:
        """Mapeia status da FlightAware para os status internos."""
        mapa = {
            "Scheduled": "confirmado",
            "En Route": "em_voo",
            "Landed": "pousado",
            "Cancelled": "cancelado",
            "Diverted": "desviado",
            "Delayed": "atrasado",
        }
        return mapa.get(status_raw, status_raw.lower())

    def nome(self) -> str:
        return "flightaware"


class AmadeusProvider(AviationProvider):
    """Provedor Amadeus para dados reais de voo.

    Requer variáveis de ambiente AMADEUS_CLIENT_ID e AMADEUS_CLIENT_SECRET.
    Documentação: https://developers.amadeus.com/
    """

    AUTH_URL = "https://api.amadeus.com/v1/security/oauth2/token"
    FLIGHTS_URL = "https://api.amadeus.com/v2/schedule/flights"

    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID", "")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET", "")
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._timeout = 15

    def _disponivel(self) -> bool:
        """Verifica se as credenciais estão configuradas."""
        return bool(self.client_id and self.client_secret)

    def _autenticar(self) -> Optional[str]:
        """Obtém ou renova token OAuth2."""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        if not self._disponivel():
            return None

        try:
            resp = requests.post(
                self.AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=self._timeout,
            )
            resp.raise_for_status()
            dados = resp.json()
            self._token = dados.get("access_token")
            expires_in = dados.get("expires_in", 1799)
            from datetime import timedelta
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            return self._token
        except Exception as e:
            logger.warning("Amadeus autenticação falhou: %s", e)
            return None

    def consultar_voo(self, codigo_reserva: str) -> Optional[dict]:
        """Amadeus requer número do voo, não código de reserva genérico."""
        return None

    def buscar_por_numero_voo(self, numero_voo: str,
                              data: Optional[str] = None) -> Optional[dict]:
        """Consulta status via Amadeus Flight Status API."""
        token = self._autenticar()
        if not token:
            return None

        try:
            # Separar companhia e número (ex: LA3456 → LA + 3456)
            import re
            match = re.match(r"([A-Z]{2})\s*(\d+)", numero_voo.upper())
            if not match:
                return None

            carrier = match.group(1)
            flight_number = match.group(2)
            data_voo = data or date.today().isoformat()

            url = (
                f"https://api.amadeus.com/v2/schedule/flights?"
                f"carrierCode={carrier}&flightNumber={flight_number}"
                f"&scheduledDepartureDate={data_voo}"
            )

            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            dados = resp.json()

            voos = dados.get("data", [])
            if not voos:
                return None

            voo = voos[0]
            partida = voo.get("flightPoints", [{}])[0] if voo.get("flightPoints") else {}
            chegada = voo.get("flightPoints", [{}])[-1] if len(voo.get("flightPoints", [])) > 1 else {}

            return {
                "numero_voo": numero_voo,
                "origem": partida.get("iataCode", "N/A"),
                "destino": chegada.get("iataCode", "N/A"),
                "horario_partida": partida.get("departure", {}).get("timings", [{}])[0].get("value", "N/A") if partida.get("departure") else "N/A",
                "horario_chegada": chegada.get("arrival", {}).get("timings", [{}])[0].get("value", "N/A") if chegada.get("arrival") else "N/A",
                "status": "confirmado",
                "motivo": "N/A",
                "provider": self.nome(),
            }
        except Exception as e:
            logger.warning("Amadeus erro: %s", e)
            return None

    def nome(self) -> str:
        return "amadeus"


class AviationService:
    """Serviço de aviação com múltiplos providers e fallback.

    Tenta providers reais primeiro, com fallback automático para
    a base simulada se nenhum provider real estiver disponível.
    """

    def __init__(self):
        self._providers: list[AviationProvider] = []
        self._fallback = SimulatedProvider()
        self._inicializar_providers()

    def _inicializar_providers(self):
        """Inicializa providers com base nas variáveis de ambiente disponíveis."""
        # FlightAware
        if os.getenv("FLIGHTAWARE_API_KEY"):
            self._providers.append(FlightAwareProvider())
            logger.info("FlightAware provider ativado")

        # Amadeus
        if os.getenv("AMADEUS_CLIENT_ID") and os.getenv("AMADEUS_CLIENT_SECRET"):
            self._providers.append(AmadeusProvider())
            logger.info("Amadeus provider ativado")

        if not self._providers:
            logger.info("Nenhum provider real configurado — usando base simulada")

    def consultar_voo(self, codigo_reserva: str) -> dict:
        """Consulta voo com fallback entre providers.

        Tenta providers reais primeiro, cai para simulado se necessário.

        Args:
            codigo_reserva: Código da reserva (6 chars).

        Returns:
            Dict com dados do voo (sempre retorna algo — nunca falha completamente).
        """
        # Tentar providers reais
        for provider in self._providers:
            try:
                resultado = provider.consultar_voo(codigo_reserva)
                if resultado:
                    logger.info("Voo encontrado via %s", provider.nome())
                    return resultado
            except Exception as e:
                logger.warning("Provider %s falhou: %s", provider.nome(), e)

        # Fallback para simulado
        resultado = self._fallback.consultar_voo(codigo_reserva)
        if resultado:
            return resultado

        return {
            "numero_voo": "N/A",
            "origem": "N/A",
            "destino": "N/A",
            "horario_partida": "N/A",
            "horario_chegada": "N/A",
            "status": "nao_encontrado",
            "motivo": f"Reserva '{codigo_reserva}' não encontrada",
            "provider": "nenhum",
        }

    def buscar_por_numero_voo(self, numero_voo: str,
                              data: Optional[str] = None) -> dict:
        """Busca por número de voo com fallback entre providers.

        Args:
            numero_voo: Código IATA do voo (ex: LA3456).
            data: Data no formato YYYY-MM-DD.

        Returns:
            Dict com dados do voo.
        """
        # Tentar providers reais
        for provider in self._providers:
            try:
                resultado = provider.buscar_por_numero_voo(numero_voo, data)
                if resultado:
                    logger.info("Voo %s encontrado via %s", numero_voo, provider.nome())
                    return resultado
            except Exception as e:
                logger.warning("Provider %s falhou para %s: %s",
                               provider.nome(), numero_voo, e)

        # Fallback simulado
        resultado = self._fallback.buscar_por_numero_voo(numero_voo, data)
        if resultado:
            return resultado

        return {
            "numero_voo": numero_voo,
            "origem": "N/A",
            "destino": "N/A",
            "horario_partida": "N/A",
            "horario_chegada": "N/A",
            "status": "nao_encontrado",
            "motivo": f"Voo '{numero_voo}' não encontrado",
            "provider": "nenhum",
        }

    @property
    def providers_ativos(self) -> list[str]:
        """Lista nomes dos providers ativos (para diagnóstico)."""
        nomes = [p.nome() for p in self._providers]
        nomes.append(self._fallback.nome())
        return nomes


# Instância global (singleton)
_service: Optional[AviationService] = None


def get_aviation_service() -> AviationService:
    """Retorna instância singleton do serviço de aviação."""
    global _service
    if _service is None:
        _service = AviationService()
    return _service
