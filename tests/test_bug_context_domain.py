"""
Bug Condition Exploration Tests - Context-Aware Domain Validation

These tests encode the EXPECTED behavior after the fix is applied.
They are EXPECTED TO FAIL on the current unfixed code, proving the bug exists.

Bug conditions:
1. validacao_node rejects follow-up messages when codigo_reserva exists in session
   but the message lacks domain keywords (e.g., "vou me atrazar o que fazer?")
2. verificar_dominio fails to recognize verb variations like "cancelar", "atrazar"
   which are not in the current PALAVRAS_CHAVE_DOMINIO list

Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
"""

from langchain_core.messages import HumanMessage

from src.agente import validacao_node
from src.validacao import verificar_dominio


class TestBugConditionSessionContext:
    """Bug Condition: Follow-up messages rejected despite session context.

    When codigo_reserva exists in session state (from a previous interaction),
    follow-up messages should be accepted even without domain keywords.
    Currently, validacao_node still calls verificar_dominio and rejects them.
    """

    def test_followup_with_session_code_atrazar(self):
        """Message 'vou me atrazar o que fazer?' with session code JKL012 should pass.

        Bug: validacao_node calls verificar_dominio even when code is from memory,
        and 'atrazar' is not in PALAVRAS_CHAVE_DOMINIO.
        Expected after fix: validacao_ok=True (domain check bypassed).
        """
        state = {
            "messages": [HumanMessage(content="vou me atrazar o que fazer?")],
            "codigo_reserva": "JKL012",
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

        result = validacao_node(state)
        assert result["validacao_ok"] is True, (
            f"Expected validacao_ok=True for follow-up with session code, "
            f"got False. Erros: {result.get('erros', [])}"
        )

    def test_followup_with_session_code_generic_question(self):
        """Message 'e agora o que posso fazer?' with session code ABC123 should pass.

        Bug: validacao_node calls verificar_dominio even when code is from memory,
        and 'e agora o que posso fazer?' has no domain keywords at all.
        Expected after fix: validacao_ok=True (domain check bypassed).
        """
        state = {
            "messages": [HumanMessage(content="e agora o que posso fazer?")],
            "codigo_reserva": "ABC123",
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

        result = validacao_node(state)
        assert result["validacao_ok"] is True, (
            f"Expected validacao_ok=True for follow-up with session code, "
            f"got False. Erros: {result.get('erros', [])}"
        )


class TestBugConditionVerbVariations:
    """Bug Condition: verificar_dominio rejects verb variations not in keyword list.

    Messages containing verb forms like 'cancelar', 'atrazar' are valid domain
    messages but are rejected because only 'cancelado'/'cancelamento' and 'atraso'
    are in PALAVRAS_CHAVE_DOMINIO.
    """

    def test_verificar_dominio_cancelar(self):
        """'meu voo vai cancelar' should be recognized as domain-relevant.

        Bug: 'cancelar' is not in PALAVRAS_CHAVE_DOMINIO (only 'cancelado'/'cancelamento').
        Expected after fix: (True, "").
        """
        resultado, erro = verificar_dominio("meu voo vai cancelar")
        assert resultado is True, (
            f"Expected verificar_dominio to accept 'meu voo vai cancelar', "
            f"got (False, '{erro}')"
        )
        assert erro == ""

    def test_verificar_dominio_atrazar(self):
        """'estou com medo de atrazar' should be recognized as domain-relevant.

        Bug: 'atrazar' (common typo) is not in PALAVRAS_CHAVE_DOMINIO.
        Expected after fix: (True, "").
        """
        resultado, erro = verificar_dominio("estou com medo de atrazar")
        assert resultado is True, (
            f"Expected verificar_dominio to accept 'estou com medo de atrazar', "
            f"got (False, '{erro}')"
        )
        assert erro == ""
