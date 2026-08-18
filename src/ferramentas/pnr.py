"""
Adaptador de integração com sistemas de reserva (PNR - Passenger Name Record).

v3.0: Permite consulta de dados completos de reserva incluindo
itinerário multi-trecho, dados do passageiro, classe, bagagem e SSR.
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


class DadosPNR:
    """Representa um registro PNR completo."""

    def __init__(self, dados: dict):
        self.localizador: str = dados.get("localizador", "")
        self.status: str = dados.get("status", "ativo")
        self.passageiro: dict = dados.get("passageiro", {})
        self.itinerario: list[dict] = dados.get("itinerario", [])
        self.contato: dict = dados.get("contato", {})
        self.pagamento: dict = dados.get("pagamento", {})
        self.servicos_especiais: list[str] = dados.get("servicos_especiais", [])
        self.bagagem: dict = dados.get("bagagem", {})
        self.observacoes: list[str] = dados.get("observacoes", [])
        self.criado_em: str = dados.get("criado_em", "")
        self.provider: str = dados.get("provider", "simulado")

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "localizador": self.localizador,
            "status": self.status,
            "passageiro": self.passageiro,
            "itinerario": self.itinerario,
            "contato": self.contato,
            "pagamento": self.pagamento,
            "servicos_especiais": self.servicos_especiais,
            "bagagem": self.bagagem,
            "observacoes": self.observacoes,
            "criado_em": self.criado_em,
            "provider": self.provider,
        }

    @property
    def primeiro_voo(self) -> dict:
        """Retorna dados do primeiro trecho do itinerário."""
        return self.itinerario[0] if self.itinerario else {}

    @property
    def ultimo_voo(self) -> dict:
        """Retorna dados do último trecho do itinerário."""
        return self.itinerario[-1] if self.itinerario else {}

    @property
    def destino_final(self) -> str:
        """Retorna o destino final da viagem."""
        if self.itinerario:
            return self.itinerario[-1].get("destino", "")
        return ""

    @property
    def nome_passageiro(self) -> str:
        """Retorna nome completo do passageiro."""
        p = self.passageiro
        return f"{p.get('nome', '')} {p.get('sobrenome', '')}".strip()


class PNRProvider(ABC):
    """Interface abstrata para provedores de dados PNR."""

    @abstractmethod
    def consultar_pnr(self, localizador: str) -> Optional[DadosPNR]:
        """Consulta PNR pelo localizador.

        Args:
            localizador: Código de reserva (6 caracteres).

        Returns:
            DadosPNR ou None se não encontrado.
        """
        ...

    @abstractmethod
    def nome(self) -> str:
        """Nome do provedor."""
        ...


class PNRSimulado(PNRProvider):
    """Provedor PNR simulado com dados de exemplo para desenvolvimento."""

    def __init__(self):
        self._base = self._gerar_base()

    def _gerar_base(self) -> dict[str, dict]:
        """Gera base simulada de PNRs."""
        hoje = date.today().isoformat()
        return {
            "ABC123": {
                "localizador": "ABC123",
                "status": "ativo",
                "passageiro": {
                    "nome": "João",
                    "sobrenome": "Silva",
                    "documento": "***.***.***-12",
                    "tipo_doc": "CPF",
                    "fidelidade": "LATAM Pass Gold",
                    "assento": "14A",
                },
                "itinerario": [
                    {
                        "trecho": 1,
                        "numero_voo": "LA3456",
                        "origem": "GRU",
                        "destino": "GIG",
                        "data": hoje,
                        "horario_partida": "14:30",
                        "horario_chegada": "15:45",
                        "classe": "Econômica",
                        "status_trecho": "cancelado",
                    }
                ],
                "contato": {
                    "email": "j***@email.com",
                    "telefone": "+55 11 9****-1234",
                },
                "pagamento": {
                    "forma": "Cartão de crédito",
                    "valor_total": "R$ 450,00",
                    "moeda": "BRL",
                    "parcelamento": "2x R$ 225,00",
                },
                "servicos_especiais": ["Refeição vegetariana"],
                "bagagem": {
                    "despachada": 1,
                    "peso_max": "23kg",
                    "mao": 1,
                },
                "observacoes": ["Passageiro frequente — prioridade no embarque"],
                "criado_em": "2024-01-15T10:30:00",
                "provider": "simulado",
            },
            "DEF456": {
                "localizador": "DEF456",
                "status": "ativo",
                "passageiro": {
                    "nome": "Maria",
                    "sobrenome": "Santos",
                    "documento": "***.***.***-56",
                    "tipo_doc": "CPF",
                    "fidelidade": "Smiles Diamante",
                    "assento": "3C",
                },
                "itinerario": [
                    {
                        "trecho": 1,
                        "numero_voo": "G3 1020",
                        "origem": "BSB",
                        "destino": "SSA",
                        "data": hoje,
                        "horario_partida": "10:00",
                        "horario_chegada": "12:30",
                        "classe": "Executiva",
                        "status_trecho": "atrasado",
                    },
                    {
                        "trecho": 2,
                        "numero_voo": "G3 2050",
                        "origem": "SSA",
                        "destino": "REC",
                        "data": hoje,
                        "horario_partida": "14:00",
                        "horario_chegada": "15:30",
                        "classe": "Executiva",
                        "status_trecho": "confirmado",
                    },
                ],
                "contato": {
                    "email": "m***@empresa.com",
                    "telefone": "+55 61 9****-5678",
                },
                "pagamento": {
                    "forma": "Milhas + Cartão",
                    "valor_total": "45.000 milhas + R$ 120,00",
                    "moeda": "BRL",
                    "parcelamento": "À vista",
                },
                "servicos_especiais": [],
                "bagagem": {
                    "despachada": 2,
                    "peso_max": "32kg",
                    "mao": 1,
                },
                "observacoes": ["Viagem corporativa", "Conexão em SSA — tempo mínimo 1h30"],
                "criado_em": "2024-01-20T14:15:00",
                "provider": "simulado",
            },
            "MNO345": {
                "localizador": "MNO345",
                "status": "ativo",
                "passageiro": {
                    "nome": "Carlos",
                    "sobrenome": "Oliveira",
                    "documento": "***.***.***-89",
                    "tipo_doc": "CPF",
                    "fidelidade": "",
                    "assento": "22F",
                },
                "itinerario": [
                    {
                        "trecho": 1,
                        "numero_voo": "G3 2078",
                        "origem": "CWB",
                        "destino": "POA",
                        "data": hoje,
                        "horario_partida": "07:00",
                        "horario_chegada": "08:20",
                        "classe": "Econômica",
                        "status_trecho": "cancelado",
                    }
                ],
                "contato": {
                    "email": "c***@email.com",
                    "telefone": "+55 41 9****-9012",
                },
                "pagamento": {
                    "forma": "PIX",
                    "valor_total": "R$ 280,00",
                    "moeda": "BRL",
                    "parcelamento": "À vista",
                },
                "servicos_especiais": ["Necessidades especiais — cadeira de rodas"],
                "bagagem": {
                    "despachada": 1,
                    "peso_max": "23kg",
                    "mao": 1,
                },
                "observacoes": [
                    "Passageiro com mobilidade reduzida",
                    "Necessita assistência no embarque e desembarque",
                ],
                "criado_em": "2024-02-01T08:45:00",
                "provider": "simulado",
            },
            "XYZ789": {
                "localizador": "XYZ789",
                "status": "ativo",
                "passageiro": {
                    "nome": "Ana",
                    "sobrenome": "Pereira",
                    "documento": "***.***.***-34",
                    "tipo_doc": "CPF",
                    "fidelidade": "LATAM Pass",
                    "assento": "8B",
                },
                "itinerario": [
                    {
                        "trecho": 1,
                        "numero_voo": "LA5678",
                        "origem": "GRU",
                        "destino": "BSB",
                        "data": hoje,
                        "horario_partida": "11:00",
                        "horario_chegada": "12:45",
                        "classe": "Premium Economy",
                        "status_trecho": "atrasado",
                    },
                    {
                        "trecho": 2,
                        "numero_voo": "LA1234",
                        "origem": "BSB",
                        "destino": "GIG",
                        "data": hoje,
                        "horario_partida": "14:30",
                        "horario_chegada": "16:15",
                        "classe": "Premium Economy",
                        "status_trecho": "confirmado",
                    },
                ],
                "contato": {
                    "email": "a***@email.com",
                    "telefone": "+55 11 9****-3456",
                },
                "pagamento": {
                    "forma": "Cartão de crédito",
                    "valor_total": "R$ 890,00",
                    "moeda": "BRL",
                    "parcelamento": "3x R$ 296,67",
                },
                "servicos_especiais": ["Assento na janela", "Refeição sem glúten"],
                "bagagem": {
                    "despachada": 1,
                    "peso_max": "23kg",
                    "mao": 1,
                },
                "observacoes": ["Conexão em BSB — risco se voo 1 atrasar > 1h"],
                "criado_em": "2024-02-10T16:20:00",
                "provider": "simulado",
            },
        }

    def consultar_pnr(self, localizador: str) -> Optional[DadosPNR]:
        """Consulta na base simulada."""
        dados = self._base.get(localizador.upper())
        if dados:
            return DadosPNR(dados)
        return None

    def nome(self) -> str:
        return "simulado"


class AmadeusPNRProvider(PNRProvider):
    """Provedor PNR via Amadeus (requer credenciais enterprise).

    Requer variáveis de ambiente:
    - AMADEUS_CLIENT_ID
    - AMADEUS_CLIENT_SECRET
    - AMADEUS_PNR_ENDPOINT (opcional, para ambiente específico)
    """

    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID", "")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET", "")
        self.endpoint = os.getenv(
            "AMADEUS_PNR_ENDPOINT",
            "https://api.amadeus.com/v1/booking/flight-orders"
        )

    @property
    def disponivel(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def consultar_pnr(self, localizador: str) -> Optional[DadosPNR]:
        """Consulta PNR via Amadeus API."""
        if not self.disponivel:
            return None

        try:
            import requests

            # Autenticação OAuth2
            auth_resp = requests.post(
                "https://api.amadeus.com/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=10,
            )
            auth_resp.raise_for_status()
            token = auth_resp.json().get("access_token")

            # Consultar PNR
            resp = requests.get(
                f"{self.endpoint}/{localizador}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            dados_raw = resp.json()

            # Transformar para formato interno
            return self._transformar_resposta(localizador, dados_raw)
        except Exception as e:
            logger.warning("Amadeus PNR erro para %s: %s", localizador, e)
            return None

    def _transformar_resposta(self, localizador: str, dados_raw: dict) -> DadosPNR:
        """Transforma resposta da API Amadeus para formato interno."""
        data = dados_raw.get("data", {})
        travelers = data.get("travelers", [{}])
        segments = []

        for offer in data.get("flightOffers", []):
            for itin in offer.get("itineraries", []):
                for seg in itin.get("segments", []):
                    segments.append({
                        "trecho": len(segments) + 1,
                        "numero_voo": f"{seg.get('carrierCode', '')}{seg.get('number', '')}",
                        "origem": seg.get("departure", {}).get("iataCode", ""),
                        "destino": seg.get("arrival", {}).get("iataCode", ""),
                        "data": seg.get("departure", {}).get("at", "")[:10],
                        "horario_partida": seg.get("departure", {}).get("at", "")[11:16],
                        "horario_chegada": seg.get("arrival", {}).get("at", "")[11:16],
                        "classe": seg.get("cabin", "Economy"),
                        "status_trecho": "confirmado",
                    })

        passageiro_raw = travelers[0] if travelers else {}
        passageiro = {
            "nome": passageiro_raw.get("name", {}).get("firstName", ""),
            "sobrenome": passageiro_raw.get("name", {}).get("lastName", ""),
            "documento": "***",
            "tipo_doc": "Passport",
            "fidelidade": "",
            "assento": "",
        }

        return DadosPNR({
            "localizador": localizador,
            "status": "ativo",
            "passageiro": passageiro,
            "itinerario": segments,
            "contato": {},
            "pagamento": {},
            "servicos_especiais": [],
            "bagagem": {},
            "observacoes": [],
            "criado_em": data.get("createdAt", ""),
            "provider": self.nome(),
        })

    def nome(self) -> str:
        return "amadeus"


class ServicoPNR:
    """Serviço PNR com múltiplos providers e fallback.

    Tenta providers reais primeiro, com fallback para simulado.
    """

    def __init__(self):
        self._providers: list[PNRProvider] = []
        self._fallback = PNRSimulado()
        self._inicializar()

    def _inicializar(self):
        """Inicializa providers disponíveis."""
        amadeus = AmadeusPNRProvider()
        if amadeus.disponivel:
            self._providers.append(amadeus)
            logger.info("Amadeus PNR provider ativado")

        if not self._providers:
            logger.info("PNR: usando base simulada (nenhum provider real)")

    def consultar(self, localizador: str) -> Optional[DadosPNR]:
        """Consulta PNR com fallback entre providers.

        Args:
            localizador: Código da reserva (6 chars).

        Returns:
            DadosPNR ou None se não encontrado em nenhum provider.
        """
        # Validar formato
        if not re.match(r'^[A-Z0-9]{6}$', localizador.upper()):
            return None

        # Tentar providers reais
        for provider in self._providers:
            try:
                resultado = provider.consultar_pnr(localizador)
                if resultado:
                    logger.info("PNR %s encontrado via %s", localizador, provider.nome())
                    return resultado
            except Exception as e:
                logger.warning("PNR provider %s falhou: %s", provider.nome(), e)

        # Fallback simulado
        resultado = self._fallback.consultar_pnr(localizador)
        if resultado:
            return resultado

        return None

    def formatar_para_contexto(self, pnr: DadosPNR) -> str:
        """Formata dados PNR para inclusão no contexto do agente.

        Args:
            pnr: Dados PNR do passageiro.

        Returns:
            String formatada com informações relevantes para o agente.
        """
        linhas = [
            f"DADOS DA RESERVA ({pnr.localizador}):",
            f"  Passageiro: {pnr.nome_passageiro}",
            f"  Status: {pnr.status}",
        ]

        if pnr.passageiro.get("fidelidade"):
            linhas.append(f"  Programa fidelidade: {pnr.passageiro['fidelidade']}")

        linhas.append(f"\n  ITINERÁRIO ({len(pnr.itinerario)} trecho(s)):")
        for trecho in pnr.itinerario:
            linhas.append(
                f"    Trecho {trecho.get('trecho', '?')}: "
                f"{trecho.get('numero_voo', 'N/A')} "
                f"{trecho.get('origem', '')} → {trecho.get('destino', '')} "
                f"| {trecho.get('data', '')} {trecho.get('horario_partida', '')} "
                f"| Classe: {trecho.get('classe', 'N/A')} "
                f"| Status: {trecho.get('status_trecho', 'N/A')}"
            )

        if pnr.servicos_especiais:
            linhas.append(f"\n  Serviços especiais: {', '.join(pnr.servicos_especiais)}")

        if pnr.bagagem:
            linhas.append(
                f"  Bagagem: {pnr.bagagem.get('despachada', 0)} desp. "
                f"({pnr.bagagem.get('peso_max', 'N/A')})"
            )

        if pnr.observacoes:
            linhas.append(f"\n  Observações: {'; '.join(pnr.observacoes)}")

        return "\n".join(linhas)

    @property
    def providers_ativos(self) -> list[str]:
        """Lista providers ativos."""
        nomes = [p.nome() for p in self._providers]
        nomes.append(self._fallback.nome())
        return nomes


# Instância singleton
_servico_pnr: Optional[ServicoPNR] = None


def get_servico_pnr() -> ServicoPNR:
    """Retorna instância singleton do serviço PNR."""
    global _servico_pnr
    if _servico_pnr is None:
        _servico_pnr = ServicoPNR()
    return _servico_pnr
