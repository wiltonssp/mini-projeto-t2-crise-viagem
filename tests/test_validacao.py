"""Testes unitários para o módulo de validação."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.validacao import (
    validar_codigo_reserva,
    validar_mensagem,
    verificar_dominio,
)


class TestValidarCodigoReserva:
    """Testes para validar_codigo_reserva."""

    def test_codigo_valido_alfanumerico(self):
        assert validar_codigo_reserva("XYZ123") == (True, "")

    def test_codigo_valido_apenas_letras(self):
        assert validar_codigo_reserva("ABCDEF") == (True, "")

    def test_codigo_valido_apenas_digitos(self):
        assert validar_codigo_reserva("123456") == (True, "")

    def test_codigo_invalido_minusculas(self):
        valido, msg = validar_codigo_reserva("abc123")
        assert valido is False
        assert "6 caracteres" in msg

    def test_codigo_invalido_menos_de_6(self):
        valido, msg = validar_codigo_reserva("ABC12")
        assert valido is False

    def test_codigo_invalido_mais_de_6(self):
        valido, msg = validar_codigo_reserva("ABC1234")
        assert valido is False

    def test_codigo_invalido_vazio(self):
        valido, msg = validar_codigo_reserva("")
        assert valido is False

    def test_codigo_invalido_caracteres_especiais(self):
        valido, msg = validar_codigo_reserva("AB-123")
        assert valido is False

    def test_codigo_invalido_espacos(self):
        valido, msg = validar_codigo_reserva("ABC 12")
        assert valido is False


class TestValidarMensagem:
    """Testes para validar_mensagem."""

    def test_mensagem_valida(self):
        assert validar_mensagem("Meu voo foi cancelado e preciso de ajuda") == (True, "")

    def test_mensagem_minima_10_chars(self):
        assert validar_mensagem("abcdefghij") == (True, "")

    def test_mensagem_maxima_2000_chars(self):
        assert validar_mensagem("a" * 2000) == (True, "")

    def test_mensagem_vazia_rejeitada(self):
        valido, msg = validar_mensagem("")
        assert valido is False
        assert "descrição válida" in msg

    def test_mensagem_apenas_espacos_rejeitada(self):
        valido, msg = validar_mensagem("     ")
        assert valido is False
        assert "descrição válida" in msg

    def test_mensagem_apenas_whitespace_rejeitada(self):
        valido, msg = validar_mensagem("  \t\n  ")
        assert valido is False
        assert "descrição válida" in msg

    def test_mensagem_curta_rejeitada(self):
        valido, msg = validar_mensagem("abc")
        assert valido is False
        assert "10 caracteres" in msg

    def test_mensagem_longa_rejeitada(self):
        valido, msg = validar_mensagem("a" * 2001)
        assert valido is False
        assert "2000 caracteres" in msg

    def test_mensagem_com_espacos_conta_nao_espaco(self):
        # 9 non-space chars with spaces -> should fail
        valido, msg = validar_mensagem("a b c d e f g h i")
        assert valido is False

    def test_mensagem_10_nao_espaco_com_espacos(self):
        # 10 non-space chars with spaces -> should pass (total < 2000)
        assert validar_mensagem("a b c d e f g h i j") == (True, "")


class TestVerificarDominio:
    """Testes para verificar_dominio."""

    def test_mensagem_com_voo(self):
        assert verificar_dominio("Meu voo foi cancelado") == (True, "")

    def test_mensagem_com_reserva(self):
        assert verificar_dominio("Preciso alterar minha reserva") == (True, "")

    def test_mensagem_com_aeroporto(self):
        assert verificar_dominio("Estou preso no aeroporto") == (True, "")

    def test_mensagem_com_bagagem(self):
        assert verificar_dominio("Minha bagagem foi extraviada") == (True, "")

    def test_mensagem_com_clima(self):
        assert verificar_dominio("O clima está afetando meu voo") == (True, "")

    def test_mensagem_com_conexao(self):
        assert verificar_dominio("Perdi minha conexão no aeroporto") == (True, "")

    def test_mensagem_com_cancelamento(self):
        assert verificar_dominio("Houve cancelamento do voo") == (True, "")

    def test_mensagem_com_embarque(self):
        assert verificar_dominio("O embarque foi adiado") == (True, "")

    def test_mensagem_fora_dominio(self):
        valido, msg = verificar_dominio("Quero saber sobre culinária italiana")
        assert valido is False
        assert "itinerários de viagem" in msg

    def test_mensagem_fora_dominio_generica(self):
        valido, msg = verificar_dominio("Qual o sentido da vida?")
        assert valido is False

    def test_case_insensitive(self):
        assert verificar_dominio("MEU VOO FOI CANCELADO") == (True, "")

    def test_mensagem_com_passageiro(self):
        assert verificar_dominio("Sou passageiro do voo LA3456") == (True, "")

    def test_mensagem_com_escala(self):
        assert verificar_dominio("Tenho uma escala em Brasília") == (True, "")
