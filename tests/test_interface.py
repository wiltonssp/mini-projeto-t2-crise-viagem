"""Testes para as interfaces CLI e Gradio."""

import sys
from unittest.mock import patch, MagicMock

import pytest


class TestCLI:
    def test_argumentos_insuficientes(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["main.py", "cli"])
        from src.interface.cli import executar_cli

        with pytest.raises(SystemExit) as exc_info:
            executar_cli()
        assert exc_info.value.code == 1

    @patch("src.interface.cli.build_graph")
    def test_execucao_com_relatorio(self, mock_build, monkeypatch, capsys):
        monkeypatch.setattr(
            sys, "argv", ["main.py", "cli", "ABC123", "meu", "voo", "cancelou"]
        )
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "relatorio_final": "Plano de contingência gerado."
        }
        mock_build.return_value = mock_graph

        from src.interface.cli import executar_cli

        executar_cli()
        captured = capsys.readouterr()
        assert "Plano de contingência" in captured.out

    @patch("src.interface.cli.build_graph")
    def test_execucao_sem_relatorio(self, mock_build, monkeypatch):
        monkeypatch.setattr(
            sys, "argv", ["main.py", "cli", "ABC123", "meu", "voo", "cancelou"]
        )
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"relatorio_final": ""}
        mock_build.return_value = mock_graph

        from src.interface.cli import executar_cli

        with pytest.raises(SystemExit) as exc_info:
            executar_cli()
        assert exc_info.value.code == 1

    @patch("src.interface.cli.build_graph")
    def test_execucao_com_excecao(self, mock_build, monkeypatch):
        monkeypatch.setattr(
            sys, "argv", ["main.py", "cli", "ABC123", "meu", "voo", "cancelou"]
        )
        mock_build.side_effect = Exception("Erro de conexão")

        from src.interface.cli import executar_cli

        with pytest.raises(SystemExit) as exc_info:
            executar_cli()
        assert exc_info.value.code == 1


class TestGradioApp:
    @patch("src.interface.gradio_app._get_graph")
    def test_responder_mensagem_vazia(self, mock_graph):
        from src.interface.gradio_app import responder

        resultado = responder("", [])
        assert "código de reserva" in resultado

    @patch("src.interface.gradio_app._get_graph")
    def test_responder_com_relatorio(self, mock_graph):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {
            "relatorio_final": "Plano gerado com sucesso."
        }
        mock_graph.return_value = mock_app

        from src.interface.gradio_app import responder

        resultado = responder("ABC123 voo cancelado por tempo ruim", [])
        assert "Plano gerado" in resultado

    @patch("src.interface.gradio_app._get_graph")
    def test_responder_fallback_mensagem_ai(self, mock_graph):
        mock_app = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = "Resposta via fallback"
        mock_app.invoke.return_value = {
            "relatorio_final": "",
            "messages": [mock_msg],
        }
        mock_graph.return_value = mock_app

        from src.interface.gradio_app import responder

        resultado = responder("ABC123 meu voo atrasou demais", [])
        assert "fallback" in resultado.lower()

    @patch("src.interface.gradio_app._get_graph")
    def test_responder_com_excecao(self, mock_graph):
        mock_app = MagicMock()
        mock_app.invoke.side_effect = Exception("API fora do ar")
        mock_graph.return_value = mock_app

        from src.interface.gradio_app import responder

        resultado = responder("ABC123 preciso de ajuda com voo", [])
        assert "Não foi possível" in resultado
        assert "API fora do ar" in resultado

    @patch("src.interface.gradio_app._get_graph")
    def test_responder_sem_relatorio_nem_mensagens(self, mock_graph):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {"relatorio_final": "", "messages": []}
        mock_graph.return_value = mock_app

        from src.interface.gradio_app import responder

        resultado = responder("ABC123 informações sobre meu voo", [])
        assert "Não foi possível" in resultado
