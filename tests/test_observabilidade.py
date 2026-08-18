"""Testes para o módulo de observabilidade."""

import json
import time

from src.observabilidade import (
    JsonFormatter,
    Trace,
    consultar_trace,
    consultar_traces_recentes,
    detectar_anomalias,
    gerar_relatorio_observabilidade,
    get_logger,
)


class TestJsonFormatter:
    """Testes para o formatter JSON."""

    def test_formato_json_valido(self):
        """Log deve produzir JSON válido."""
        import logging

        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="test.py", lineno=1,
            msg="Mensagem de teste", args=None, exc_info=None,
        )
        resultado = formatter.format(record)
        dados = json.loads(resultado)
        assert dados["level"] == "INFO"
        assert dados["message"] == "Mensagem de teste"
        assert "timestamp" in dados

    def test_inclui_campos_extras(self):
        """Campos extras (trace_id, node, latency) devem aparecer no JSON."""
        import logging

        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="test.py", lineno=1,
            msg="Node executado", args=None, exc_info=None,
        )
        record.trace_id = "abc12345"
        record.node = "consulta_voo"
        record.latency_ms = 150.5
        resultado = formatter.format(record)
        dados = json.loads(resultado)
        assert dados["trace_id"] == "abc12345"
        assert dados["node"] == "consulta_voo"
        assert dados["latency_ms"] == 150.5


class TestTrace:
    """Testes para o sistema de traces."""

    def test_cria_trace_com_id(self):
        """Trace deve ter um ID único."""
        trace = Trace()
        assert trace.trace_id is not None
        assert len(trace.trace_id) == 8

    def test_span_registra_latencia(self):
        """Span deve registrar latência de execução."""
        trace = Trace()
        with trace.span("test_node", "input_test") as span_data:
            time.sleep(0.01)  # Simular trabalho
            span_data["output"] = "resultado"

        assert len(trace.nodes) == 1
        assert trace.nodes[0]["node"] == "test_node"
        assert trace.nodes[0]["status"] == "OK"
        assert trace.nodes[0]["latency_ms"] > 0

    def test_span_captura_erro(self):
        """Span deve capturar erros e marcar status como ERROR."""
        trace = Trace()
        try:
            with trace.span("node_falho") as span_data:
                raise ValueError("Erro simulado")
        except ValueError:
            pass

        assert len(trace.nodes) == 1
        assert trace.nodes[0]["status"] == "ERROR"
        assert trace.nodes[0]["error"] == "Erro simulado"

    def test_finalizar_retorna_resumo(self):
        """Finalizar deve retornar resumo da execução."""
        trace = Trace()
        with trace.span("node_1") as _:
            pass
        with trace.span("node_2") as _:
            pass

        resumo = trace.finalizar()
        assert resumo["trace_id"] == trace.trace_id
        assert resumo["total_nodes"] == 2
        assert resumo["nodes_ok"] == 2
        assert resumo["nodes_error"] == 0
        assert resumo["total_latency_ms"] >= 0

    def test_multiplos_spans_correlacionados(self):
        """Múltiplos spans devem compartilhar o mesmo trace_id."""
        trace = Trace()
        with trace.span("node_a") as _:
            pass
        with trace.span("node_b") as _:
            pass

        # Todos os nodes têm o mesmo trace_id
        for node in trace.nodes:
            assert node["trace_id"] == trace.trace_id


class TestConsultaTraces:
    """Testes para consulta de traces persistidos."""

    def test_consultar_trace_existente(self):
        """Deve retornar registros de um trace persistido."""
        trace = Trace()
        with trace.span("test_persist") as span_data:
            span_data["output"] = "ok"
        trace.finalizar()

        registros = consultar_trace(trace.trace_id)
        assert len(registros) >= 1
        assert registros[0]["trace_id"] == trace.trace_id

    def test_consultar_trace_inexistente(self):
        """Deve retornar lista vazia para trace inexistente."""
        registros = consultar_trace("nao_existe")
        assert registros == []

    def test_consultar_traces_recentes(self):
        """Deve retornar lista de traces recentes."""
        # Criar um trace para garantir que existe algo
        trace = Trace()
        with trace.span("recente") as _:
            pass
        trace.finalizar()

        recentes = consultar_traces_recentes(5)
        assert isinstance(recentes, list)
        assert len(recentes) >= 1


class TestDetectarAnomalias:
    """Testes para detecção de anomalias."""

    def test_retorna_lista(self):
        """Deve sempre retornar uma lista (mesmo vazia)."""
        resultado = detectar_anomalias(janela_minutos=1)
        assert isinstance(resultado, list)


class TestRelatorioObservabilidade:
    """Testes para geração de relatório."""

    def test_relatorio_geral(self):
        """Relatório geral deve ser Markdown válido."""
        relatorio = gerar_relatorio_observabilidade()
        assert "Observabilidade" in relatorio or "Nenhum" in relatorio

    def test_relatorio_trace_especifico(self):
        """Relatório de trace específico deve mostrar detalhes."""
        trace = Trace()
        with trace.span("node_relatorio") as _:
            pass
        trace.finalizar()

        relatorio = gerar_relatorio_observabilidade(trace.trace_id)
        assert trace.trace_id in relatorio
        assert "node_relatorio" in relatorio

    def test_relatorio_trace_inexistente(self):
        """Relatório de trace inexistente deve informar."""
        relatorio = gerar_relatorio_observabilidade("nao_existe_xyz")
        assert "Nenhum" in relatorio


class TestGetLogger:
    """Testes para o logger singleton."""

    def test_retorna_logger(self):
        """Deve retornar um logger configurado."""
        logger = get_logger()
        assert logger is not None
        assert logger.name == "viagem_inteligente"

    def test_singleton(self):
        """Deve retornar a mesma instância."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
