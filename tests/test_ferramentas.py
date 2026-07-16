"""Testes para as ferramentas (voo, clima, transporte)."""

from unittest.mock import patch, MagicMock

from src.ferramentas.voo import consultar_status_voo, VOOS_DB
from src.ferramentas.clima import (
    consultar_clima,
    _mapear_condicao,
    _detectar_condicoes_adversas,
    _formatar_clima,
)
from src.ferramentas.transporte import (
    consultar_transporte_alternativo,
    _duracao_para_minutos,
)


# --- Voo ---

class TestConsultarStatusVoo:
    def test_reserva_existente(self):
        resultado = consultar_status_voo.invoke({"codigo_reserva": "ABC123"})
        assert "LA3456" in resultado
        assert "cancelado" in resultado
        assert "GRU" in resultado

    def test_reserva_inexistente(self):
        resultado = consultar_status_voo.invoke({"codigo_reserva": "ZZZ999"})
        assert "não encontrada" in resultado

    def test_todos_voos_tem_campos(self):
        for codigo, voo in VOOS_DB.items():
            assert "numero_voo" in voo
            assert "status" in voo


# --- Clima ---

class TestMapearCondicao:
    def test_ceu_limpo(self):
        assert _mapear_condicao(0) == "Céu limpo"

    def test_nublado(self):
        assert _mapear_condicao(2) == "Parcialmente nublado"

    def test_neblina(self):
        assert _mapear_condicao(45) == "Neblina"

    def test_garoa(self):
        assert _mapear_condicao(53) == "Garoa"

    def test_chuva(self):
        assert _mapear_condicao(63) == "Chuva"

    def test_neve(self):
        assert _mapear_condicao(75) == "Neve"

    def test_pancadas(self):
        assert _mapear_condicao(81) == "Pancadas de chuva"

    def test_tempestade(self):
        assert _mapear_condicao(95) == "Tempestade"

    def test_desconhecido(self):
        assert _mapear_condicao(999) == "Condição desconhecida"


class TestDetectarCondicoesAdversas:
    def test_tempestade(self):
        alertas = _detectar_condicoes_adversas(96, 5000, 30)
        assert any("Tempestade" in a for a in alertas)

    def test_neve(self):
        alertas = _detectar_condicoes_adversas(75, 5000, 20)
        assert any("Neve" in a for a in alertas)

    def test_neblina_densa(self):
        alertas = _detectar_condicoes_adversas(45, 500, 10)
        assert any("Neblina" in a for a in alertas)

    def test_ventos_fortes(self):
        alertas = _detectar_condicoes_adversas(0, 10000, 70)
        assert any("Ventos" in a for a in alertas)

    def test_chuva_intensa(self):
        alertas = _detectar_condicoes_adversas(65, 5000, 20)
        assert any("Chuva" in a for a in alertas)

    def test_sem_alertas(self):
        alertas = _detectar_condicoes_adversas(0, 10000, 10)
        assert alertas == []


class TestFormatarClima:
    def test_formatacao_sem_alertas(self):
        current = {
            "temperature_2m": 25.0,
            "weather_code": 0,
            "wind_speed_10m": 10,
            "visibility": 10000,
        }
        resultado = _formatar_clima(current, "GRU")
        assert "GRU" in resultado
        assert "25.0°C" in resultado
        assert "Céu limpo" in resultado
        assert "Sem condições adversas" in resultado

    def test_formatacao_com_alertas(self):
        current = {
            "temperature_2m": 18.0,
            "weather_code": 95,
            "wind_speed_10m": 70,
            "visibility": 3000,
        }
        resultado = _formatar_clima(current, "GIG")
        assert "CONDIÇÕES ADVERSAS" in resultado
        assert "Tempestade" in resultado


class TestConsultarClimaAPI:
    @patch("src.ferramentas.clima.requests.get")
    def test_consulta_sucesso(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "current": {
                "temperature_2m": 22.0,
                "weather_code": 0,
                "wind_speed_10m": 15,
                "visibility": 8000,
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        resultado = consultar_clima.invoke({"codigo_aeroporto": "GRU"})
        assert "GRU" in resultado
        assert "22.0°C" in resultado

    @patch("src.ferramentas.clima.requests.get")
    def test_consulta_timeout(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        resultado = consultar_clima.invoke({"codigo_aeroporto": "GRU"})
        assert "timeout" in resultado

    @patch("src.ferramentas.clima.requests.get")
    def test_consulta_connection_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        resultado = consultar_clima.invoke({"codigo_aeroporto": "GRU"})
        assert "falha na conexão" in resultado

    def test_aeroporto_invalido(self):
        resultado = consultar_clima.invoke({"codigo_aeroporto": "XXX"})
        assert "não encontrado" in resultado


# --- Transporte ---

class TestDuracaoParaMinutos:
    def test_horas_e_minutos(self):
        assert _duracao_para_minutos("1h15min") == 75

    def test_apenas_horas(self):
        assert _duracao_para_minutos("2h00min") == 120

    def test_apenas_minutos(self):
        assert _duracao_para_minutos("45min") == 45

    def test_formato_invalido(self):
        # Sem "h" nem "min" retorna 0
        assert _duracao_para_minutos("invalid") == 0


class TestConsultarTransporte:
    def test_rota_existente(self):
        resultado = consultar_transporte_alternativo.invoke(
            {"origem": "GRU", "destino": "GIG"}
        )
        assert "GRU" in resultado
        assert "GIG" in resultado
        assert "VOO" in resultado or "ONIBUS" in resultado

    def test_rota_inexistente(self):
        resultado = consultar_transporte_alternativo.invoke(
            {"origem": "GRU", "destino": "XXX"}
        )
        assert "Nenhuma opção" in resultado

    def test_case_insensitive(self):
        resultado = consultar_transporte_alternativo.invoke(
            {"origem": "gru", "destino": "gig"}
        )
        assert "GRU" in resultado

    def test_ordenacao_por_duracao(self):
        resultado = consultar_transporte_alternativo.invoke(
            {"origem": "GRU", "destino": "GIG"}
        )
        # Primeiro resultado deve ser o mais rápido (voo)
        linhas = resultado.strip().split("\n")
        assert "VOO" in linhas[1]  # primeira opção após cabeçalho
