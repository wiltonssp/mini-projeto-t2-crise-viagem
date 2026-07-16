"""Testes para os nós do agente (grafo LangGraph)."""

from unittest.mock import patch, MagicMock

from langchain_core.messages import HumanMessage, AIMessage

from src.agente import (
    validacao_node,
    consulta_voo_node,
    consulta_clima_node,
    consulta_transporte_node,
    rag_node,
    analise_llm_node,
    gerar_plano_node,
    erro_node,
    build_graph,
    roteador_validacao,
    _extrair_codigo_reserva,
    _extrair_mensagem,
    _parse_status_voo,
    _parse_clima,
    _parse_transporte,
    _eh_pergunta_simples,
    _eh_pergunta_sobre_voo,
    _eh_consulta_clima_direta,
)


def _state_base(msg="ABC123 meu voo foi cancelado por mau tempo", **kwargs):
    """Cria estado base para testes."""
    state = {
        "messages": [HumanMessage(content=msg)],
        "codigo_reserva": "",
        "mensagem_usuario": "",
        "dados_cliente": {},
        "status_voo": {},
        "info_clima": {},
        "alternativas_transporte": [],
        "politicas_recuperadas": [],
        "direitos_passageiro": [],
        "relatorio_final": "",
        "erros": [],
        "validacao_ok": False,
    }
    state.update(kwargs)
    return state


# --- Funções auxiliares ---

class TestExtrairCodigoReserva:
    def test_extrai_codigo_valido(self):
        assert _extrair_codigo_reserva("ABC123 meu voo") == "ABC123"

    def test_codigo_no_meio(self):
        assert _extrair_codigo_reserva("meu voo JKL012 atrasou") == "JKL012"

    def test_sem_codigo(self):
        assert _extrair_codigo_reserva("meu voo atrasou") == ""

    def test_ignora_palavras_comuns(self):
        # Palavra comum de 6 letras misturada em texto não deve ser extraída
        # quando não tem mistura letras+dígitos (o regex exige boundary match)
        assert _extrair_codigo_reserva("olá bom dia") == ""


class TestExtrairMensagem:
    def test_remove_codigo(self):
        assert _extrair_mensagem("ABC123 meu voo", "ABC123") == "meu voo"

    def test_mensagem_sem_codigo(self):
        assert _extrair_mensagem("meu voo atrasou", "") == "meu voo atrasou"


class TestParseStatusVoo:
    def test_parseia_corretamente(self):
        texto = "Voo: LA3456\nOrigem: GRU\nDestino: GIG\nStatus: cancelado"
        dados = _parse_status_voo(texto)
        assert dados["voo"] == "LA3456"
        assert dados["origem"] == "GRU"
        assert dados["status"] == "cancelado"


class TestParseClima:
    def test_detecta_adversas(self):
        texto = "Clima em GRU:\n  Temperatura: 20°C\n  ⚠️ CONDIÇÕES ADVERSAS DETECTADAS:"
        dados = _parse_clima(texto)
        assert dados["condicoes_adversas"] is True

    def test_sem_adversas(self):
        texto = "Clima em GRU:\n  Temperatura: 25°C\n  ✅ Sem condições adversas"
        dados = _parse_clima(texto)
        assert dados["condicoes_adversas"] is False


class TestParseTransporte:
    def test_extrai_opcoes(self):
        texto = "Opções:\n  1. VOO GRU→GIG\n  2. ONIBUS GRU→GIG"
        opcoes = _parse_transporte(texto)
        assert len(opcoes) == 2

    def test_sem_numeracao(self):
        texto = "Nenhuma opção encontrada"
        opcoes = _parse_transporte(texto)
        assert opcoes == [texto]


class TestEhPerguntaSimples:
    def test_perguntas_simples(self):
        assert _eh_pergunta_simples("qual o status do meu voo") is True
        assert _eh_pergunta_simples("status do meu voo") is True
        assert _eh_pergunta_simples("quando sai meu voo?") is True
        assert _eh_pergunta_simples("qual a data do voo?") is True

    def test_nao_simples_crise(self):
        assert _eh_pergunta_simples("meu voo foi cancelado o que fazer") is False
        assert _eh_pergunta_simples("preciso de ajuda urgente") is False
        assert _eh_pergunta_simples("quais meus direitos de reembolso") is False


class TestEhPerguntaSobreVoo:
    def test_detecta_perguntas_voo(self):
        assert _eh_pergunta_sobre_voo("meu voo atrasou") is True
        assert _eh_pergunta_sobre_voo("status do meu voo") is True
        assert _eh_pergunta_sobre_voo("minha reserva está ok?") is True

    def test_nao_detecta_outros(self):
        assert _eh_pergunta_sobre_voo("olá tudo bem?") is False


class TestEhConsultaClimaDireta:
    def test_clima_cidade(self):
        eh, codigo = _eh_consulta_clima_direta("previsão do tempo em São Paulo")
        assert eh is True
        assert codigo == "GRU"

    def test_clima_destino(self):
        eh, codigo = _eh_consulta_clima_direta("como está o clima no destino")
        assert eh is True
        assert codigo == "DESTINO_MEMORIA"

    def test_nao_clima(self):
        eh, codigo = _eh_consulta_clima_direta("meu voo foi cancelado")
        assert eh is False


# --- Nós do grafo ---

class TestValidacaoNode:
    def test_validacao_ok_com_codigo_e_dominio(self):
        state = _state_base("ABC123 meu voo foi cancelado por mau tempo")
        result = validacao_node(state)
        assert result["validacao_ok"] is True
        assert result["codigo_reserva"] == "ABC123"

    def test_validacao_falha_sem_codigo(self):
        state = _state_base("meu voo foi cancelado por mau tempo")
        result = validacao_node(state)
        assert result["validacao_ok"] is False

    def test_validacao_usa_codigo_memoria(self):
        state = _state_base(
            "e agora o que posso fazer?",
            codigo_reserva="JKL012",
        )
        result = validacao_node(state)
        assert result["validacao_ok"] is True

    def test_validacao_codigo_direto_pula_dominio(self):
        state = _state_base("JKL012 qual o status?")
        result = validacao_node(state)
        assert result["validacao_ok"] is True

    def test_validacao_clima_direta_cidade(self):
        state = _state_base("previsão do tempo em São Paulo")
        result = validacao_node(state)
        assert result["validacao_ok"] is True
        assert result["status_voo"]["destino"] == "GRU"

    def test_validacao_clima_direta_destino_com_memoria(self):
        state = _state_base(
            "como está o tempo no destino",
            codigo_reserva="ABC123",
            status_voo={"destino": "GIG", "origem": "GRU"},
        )
        result = validacao_node(state)
        assert result["validacao_ok"] is True

    def test_validacao_clima_direta_destino_sem_memoria(self):
        state = _state_base("como está o clima no destino")
        result = validacao_node(state)
        assert result["validacao_ok"] is False

    def test_validacao_sem_mensagem(self):
        state = _state_base("")
        state["messages"] = []
        result = validacao_node(state)
        assert result["validacao_ok"] is False


class TestConsultaVooNode:
    def test_consulta_voo_existente(self):
        state = _state_base(codigo_reserva="ABC123")
        result = consulta_voo_node(state)
        assert result["status_voo"]["voo"] == "LA3456"
        assert result["status_voo"]["status"] == "cancelado"

    def test_consulta_voo_sem_codigo(self):
        state = _state_base(codigo_reserva="")
        result = consulta_voo_node(state)
        assert result == {}


class TestConsultaClimaNode:
    @patch("src.agente.consultar_clima")
    def test_consulta_clima_com_destino(self, mock_clima):
        mock_clima.invoke.return_value = (
            "Clima em GIG:\n  Temperatura: 28°C\n  Condição: Céu limpo\n"
            "  Vento: 10 km/h\n  Visibilidade: 10000m\n  ✅ Sem condições adversas"
        )
        state = _state_base(status_voo={"destino": "GIG"})
        result = consulta_clima_node(state)
        assert "info_clima" in result
        assert result["info_clima"]["condicoes_adversas"] is False

    def test_consulta_clima_sem_destino(self):
        state = _state_base(status_voo={})
        result = consulta_clima_node(state)
        assert "erro" in result["info_clima"]


class TestConsultaTransporteNode:
    @patch("src.agente.consultar_transporte_alternativo")
    def test_com_origem_destino(self, mock_transp):
        mock_transp.invoke.return_value = (
            "Opções:\n  1. [VOO] GRU→GIG Duração: 1h15min\n"
            "  2. [ONIBUS] GRU→GIG Duração: 6h"
        )
        state = _state_base(status_voo={"origem": "GRU", "destino": "GIG"})
        result = consulta_transporte_node(state)
        assert len(result["alternativas_transporte"]) == 2

    def test_sem_origem_destino(self):
        state = _state_base(status_voo={})
        result = consulta_transporte_node(state)
        assert "indisponíveis" in result["alternativas_transporte"][0].lower()


class TestRagNode:
    def test_retorna_politicas(self):
        state = _state_base(
            status_voo={"status": "cancelado", "motivo": "mau tempo"},
            mensagem_usuario="voo cancelado",
        )
        result = rag_node(state)
        assert "politicas_recuperadas" in result
        assert isinstance(result["politicas_recuperadas"], list)


class TestAnaliseLlmNode:
    @patch("src.agente._get_llm")
    def test_analise_retorna_mensagem(self, mock_llm):
        mock_chat = MagicMock()
        mock_chat.invoke.return_value = MagicMock(content="Análise concluída.")
        mock_llm.return_value = mock_chat

        state = _state_base(
            status_voo={"status": "cancelado"},
            info_clima={},
            alternativas_transporte=[],
            politicas_recuperadas=[],
            direitos_passageiro=[],
            mensagem_usuario="meu voo cancelou",
            erros=[],
        )
        result = analise_llm_node(state)
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)


class TestGerarPlanoNode:
    @patch("src.agente._get_llm")
    def test_gera_plano_crise(self, mock_llm):
        mock_chat = MagicMock()
        mock_chat.invoke.return_value = MagicMock(
            content="## 1. Diagnóstico\nVoo cancelado."
        )
        mock_llm.return_value = mock_chat

        state = _state_base(
            status_voo={"voo": "LA3456", "status": "cancelado", "motivo": "mau tempo",
                        "origem": "GRU", "destino": "GIG", "partida": "14:30",
                        "chegada": "15:45"},
            info_clima={"texto_completo": "Chuva forte"},
            alternativas_transporte=["1. VOO"],
            politicas_recuperadas=[{"titulo": "Reembolso", "conteudo": "7 dias"}],
            direitos_passageiro=[{"titulo": "ANAC", "conteudo": "Resolução 400"}],
            mensagem_usuario="meu voo foi cancelado preciso de ajuda",
            erros=[],
        )
        result = gerar_plano_node(state)
        assert "relatorio_final" in result
        assert "Diagnóstico" in result["relatorio_final"]

    @patch("src.agente._get_llm")
    def test_gera_resposta_direta_pergunta_simples(self, mock_llm):
        mock_chat = MagicMock()
        mock_chat.invoke.return_value = MagicMock(
            content="Seu voo LA1234 está embarcando."
        )
        mock_llm.return_value = mock_chat

        state = _state_base(
            status_voo={"voo": "LA1234", "status": "embarcando"},
            info_clima={},
            alternativas_transporte=[],
            politicas_recuperadas=[],
            direitos_passageiro=[],
            mensagem_usuario="qual o status do meu voo?",
            erros=[],
        )
        result = gerar_plano_node(state)
        assert "relatorio_final" in result
        assert "embarcando" in result["relatorio_final"]

    def test_gera_plano_com_erro(self):
        """Testa fallback de erro quando LLM falha."""
        with patch("src.agente._get_llm") as mock_llm:
            mock_llm.side_effect = Exception("API indisponível")
            state = _state_base(
                status_voo={},
                info_clima={},
                alternativas_transporte=[],
                politicas_recuperadas=[],
                direitos_passageiro=[],
                mensagem_usuario="meu voo foi cancelado preciso ajuda urgente",
                erros=[],
            )
            result = gerar_plano_node(state)
            assert "Erro" in result["relatorio_final"]


class TestErroNode:
    def test_gera_mensagem_erro(self):
        state = _state_base(
            erros=[{"nó": "validacao", "erro": "Código inválido."}]
        )
        result = erro_node(state)
        assert "Código inválido" in result["relatorio_final"]

    def test_erro_sem_detalhes(self):
        state = _state_base(erros=[])
        result = erro_node(state)
        assert "Não foi possível" in result["relatorio_final"]


class TestRoteadorValidacao:
    def test_direciona_ok(self):
        assert roteador_validacao({"validacao_ok": True}) == "consulta_voo"

    def test_direciona_erro(self):
        assert roteador_validacao({"validacao_ok": False}) == "erro"


class TestBuildGraph:
    def test_grafo_compila(self):
        graph = build_graph()
        assert graph is not None
