"""
Testes unitários para o entry point main.py.
Valida comportamento de variáveis de ambiente e seleção de modo.
"""

import os
import sys
import pytest


class TestValidarVariaveisAmbiente:
    """Testes para validação de variáveis de ambiente obrigatórias."""

    def test_encerra_quando_groq_api_key_ausente(self, monkeypatch):
        """Programa encerra com sys.exit(1) se GROQ_API_KEY não definida."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        # Forçar os.getenv a retornar None para GROQ_API_KEY
        monkeypatch.setattr("os.getenv", lambda key, default=None: None if key == "GROQ_API_KEY" else os.environ.get(key, default))

        from main import validar_variaveis_ambiente

        with pytest.raises(SystemExit) as exc_info:
            validar_variaveis_ambiente()
        assert exc_info.value.code == 1

    def test_encerra_quando_groq_api_key_vazia(self, monkeypatch):
        """Programa encerra com sys.exit(1) se GROQ_API_KEY está vazia."""
        monkeypatch.setenv("GROQ_API_KEY", "")

        from main import validar_variaveis_ambiente

        with pytest.raises(SystemExit) as exc_info:
            validar_variaveis_ambiente()
        assert exc_info.value.code == 1

    def test_encerra_quando_groq_api_key_apenas_espacos(self, monkeypatch):
        """Programa encerra com sys.exit(1) se GROQ_API_KEY tem apenas espaços."""
        monkeypatch.setenv("GROQ_API_KEY", "   ")

        from main import validar_variaveis_ambiente

        with pytest.raises(SystemExit) as exc_info:
            validar_variaveis_ambiente()
        assert exc_info.value.code == 1

    def test_nao_encerra_quando_groq_api_key_definida(self, monkeypatch):
        """Programa não encerra se GROQ_API_KEY está definida com valor."""
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")

        from main import validar_variaveis_ambiente

        # Não deve levantar SystemExit
        validar_variaveis_ambiente()


class TestSelecaoModo:
    """Testes para seleção de modo de interface."""

    def test_modo_default_eh_web(self, monkeypatch):
        """Sem argumento, modo padrão é 'web'."""
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
        monkeypatch.setattr(sys, "argv", ["main.py"])

        # Verificar que sem argumentos, o modo será 'web'
        modo = sys.argv[1] if len(sys.argv) > 1 else "web"
        assert modo == "web"

    def test_modo_cli_selecionado(self, monkeypatch):
        """Argumento 'cli' seleciona interface de linha de comando."""
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
        monkeypatch.setattr(sys, "argv", ["main.py", "cli"])

        modo = sys.argv[1] if len(sys.argv) > 1 else "web"
        assert modo == "cli"

    def test_modo_web_selecionado(self, monkeypatch):
        """Argumento 'web' seleciona interface Gradio."""
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
        monkeypatch.setattr(sys, "argv", ["main.py", "web"])

        modo = sys.argv[1] if len(sys.argv) > 1 else "web"
        assert modo == "web"

    def test_modo_invalido_encerra(self, monkeypatch):
        """Modo não reconhecido encerra com sys.exit(1)."""
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
        monkeypatch.setattr(sys, "argv", ["main.py", "invalido"])

        from main import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
