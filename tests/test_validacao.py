"""Testes para o módulo de validação."""

from src.validacao import validar_codigo_reserva, validar_mensagem, verificar_dominio


class TestValidarCodigoReserva:
    def test_codigo_valido(self):
        assert validar_codigo_reserva("XYZ123") == (True, "")
        assert validar_codigo_reserva("ABCDEF") == (True, "")
        assert validar_codigo_reserva("123456") == (True, "")

    def test_codigo_invalido(self):
        for code in ["abc123", "ABC12", "ABC1234", "", "AB-123", "ABC 12"]:
            valido, _ = validar_codigo_reserva(code)
            assert valido is False, f"Deveria rejeitar: {code}"


class TestValidarMensagem:
    def test_mensagem_valida(self):
        assert validar_mensagem("Meu voo foi cancelado") == (True, "")
        assert validar_mensagem("abcdefghij") == (True, "")

    def test_mensagem_invalida(self):
        valido, msg = validar_mensagem("")
        assert valido is False
        valido, msg = validar_mensagem("   ")
        assert valido is False
        valido, msg = validar_mensagem("abc")
        assert valido is False
        valido, msg = validar_mensagem("a" * 2001)
        assert valido is False


class TestVerificarDominio:
    def test_aceita_palavras_chave(self):
        palavras = ["voo", "viagem", "aeroporto", "reserva", "bagagem",
                    "cancelado", "atraso", "embarque", "cancelar", "atrazar"]
        for p in palavras:
            valido, _ = verificar_dominio(f"Preciso de ajuda com {p} agora")
            assert valido is True, f"Deveria aceitar: {p}"

    def test_rejeita_fora_dominio(self):
        valido, msg = verificar_dominio("qual a receita de bolo de chocolate?")
        assert valido is False
        assert "itinerários de viagem" in msg
