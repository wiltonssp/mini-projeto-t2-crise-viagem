"""
Preservation property tests - Non-Buggy Behavior Unchanged.

These tests capture the EXISTING behavior on UNFIXED code.
They must PASS on the current code to confirm baseline behavior to preserve.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
"""

import sys
import os
import string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from langchain_core.messages import HumanMessage

from src.validacao import (
    validar_codigo_reserva,
    validar_mensagem,
    verificar_dominio,
    PALAVRAS_CHAVE_DOMINIO,
)
from src.agente import validacao_node


# ---------------------------------------------------------------------------
# Helper strategies and constants
# ---------------------------------------------------------------------------

# The original domain keywords that must continue being accepted
ORIGINAL_KEYWORDS = [
    "viagem", "voo", "aeroporto", "conexão", "conexao",
    "itinerário", "itinerario", "reserva", "bagagem",
    "transporte", "clima", "cancelado", "cancelamento",
    "atraso", "atrasado", "embarque", "escala", "mala",
    "passagem", "passageiro", "companhia", "aerea", "aérea",
]

# Words that should NOT trigger domain acceptance (unrelated topics)
NON_DOMAIN_WORDS = [
    "receita", "bolo", "chocolate", "futebol", "musica", "filme",
    "politica", "economia", "filosofia", "matematica", "historia",
    "computador", "celular", "gato", "cachorro", "carro", "casa",
    "escola", "trabalho", "dinheiro", "comida", "livro", "jogo",
]


def _make_empty_state(message_text: str) -> dict:
    """Create an empty validacao_node state with a given message."""
    return {
        "messages": [HumanMessage(content=message_text)],
        "codigo_reserva": "",  # EMPTY - no session context
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


def _message_contains_domain_keyword(msg: str) -> bool:
    """Check if message contains any ORIGINAL domain keyword."""
    msg_lower = msg.lower()
    return any(kw in msg_lower for kw in ORIGINAL_KEYWORDS)


def _message_has_valid_code(msg: str) -> bool:
    """Check if message contains a potential 6-char alphanumeric code."""
    import re
    return bool(re.search(r'\b[A-Z0-9]{6}\b', msg))


# Strategy: random text WITHOUT any domain keywords
@st.composite
def non_domain_messages(draw):
    """Generate messages that do NOT contain any domain keyword."""
    # Build from safe non-domain words
    num_words = draw(st.integers(min_value=3, max_value=8))
    words = [draw(st.sampled_from(NON_DOMAIN_WORDS)) for _ in range(num_words)]
    msg = " ".join(words)
    # Double check no keyword snuck in
    assume(not _message_contains_domain_keyword(msg))
    return msg


# Strategy: generate messages with at least one original keyword
@st.composite
def messages_with_keyword(draw):
    """Generate messages containing at least one original domain keyword."""
    keyword = draw(st.sampled_from(ORIGINAL_KEYWORDS))
    # Add some padding text around the keyword (10+ chars total)
    prefix = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L", "Zs"), whitelist_characters=" "),
        min_size=5, max_size=20
    ))
    suffix = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L", "Zs"), whitelist_characters=" "),
        min_size=5, max_size=20
    ))
    msg = f"{prefix} {keyword} {suffix}"
    # Ensure >= 10 non-space chars for validar_mensagem
    non_space = len(msg.replace(" ", "").replace("\t", "").replace("\n", ""))
    assume(non_space >= 10)
    assume(len(msg) <= 2000)
    return msg


# Strategy: short messages (fewer than 10 non-space characters)
@st.composite
def short_messages(draw):
    """Generate messages with fewer than 10 non-space characters."""
    # Generate 1-9 non-space characters
    num_chars = draw(st.integers(min_value=1, max_value=9))
    chars = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L",)),
        min_size=num_chars, max_size=num_chars
    ))
    # Optionally add spaces
    spaces = draw(st.text(alphabet=" ", min_size=0, max_size=5))
    msg = spaces + chars + spaces
    # Confirm fewer than 10 non-space chars
    non_space = len(msg.replace(" ", "").replace("\t", "").replace("\n", ""))
    assume(0 < non_space < 10)
    return msg


# ---------------------------------------------------------------------------
# Observation tests (specific examples on unfixed code)
# ---------------------------------------------------------------------------

class TestPreservationObservations:
    """Observe specific behaviors on UNFIXED code to confirm baseline."""

    def test_out_of_domain_rejected(self):
        """verificar_dominio rejects unrelated messages."""
        valido, msg = verificar_dominio("qual a receita de bolo de chocolate?")
        assert valido is False
        assert "Desculpe" in msg

    def test_domain_keyword_accepted(self):
        """verificar_dominio accepts messages with existing keywords."""
        valido, msg = verificar_dominio("Meu voo foi cancelado e preciso de ajuda")
        assert valido is True
        assert msg == ""

    def test_code_format_validation_preserved(self):
        """validar_codigo_reserva validates 6 uppercase alphanum codes."""
        valido, msg = validar_codigo_reserva("XYZ123")
        assert valido is True
        assert msg == ""

    def test_minimum_size_validation_preserved(self):
        """validar_mensagem rejects messages with < 10 non-space chars."""
        valido, msg = validar_mensagem("abc")
        assert valido is False
        assert "10 caracteres" in msg

    def test_validacao_node_rejects_without_context(self):
        """validacao_node with empty state and no-domain message → rejected."""
        state = _make_empty_state("qual o sentido da vida e do universo?")
        result = validacao_node(state)
        assert result["validacao_ok"] is False

    def test_validacao_node_rejects_recipe_question(self):
        """validacao_node rejects recipe question without any context."""
        state = _make_empty_state("qual a receita de bolo de chocolate maranhense?")
        result = validacao_node(state)
        assert result["validacao_ok"] is False


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

class TestPreservationProperties:
    """Property-based tests for preservation of existing behavior."""

    @given(msg=non_domain_messages())
    @settings(max_examples=50, deadline=None)
    def test_no_keyword_no_session_rejected_by_validacao_node(self, msg: str):
        """
        **Validates: Requirements 3.1, 3.2**

        For all random messages without any domain keyword AND without
        codigo_reserva in session → validacao_node rejects.

        Note: Without a valid code in the message or session, validacao_node
        rejects at the code validation step (before domain check). This is
        still a rejection that must be preserved.
        """
        state = _make_empty_state(msg)
        result = validacao_node(state)
        assert result["validacao_ok"] is False

    @given(msg=messages_with_keyword())
    @settings(max_examples=50, deadline=None)
    def test_original_keywords_accepted_by_verificar_dominio(self, msg: str):
        """
        **Validates: Requirements 3.3**

        For all messages containing at least one original PALAVRAS_CHAVE_DOMINIO
        keyword → verificar_dominio returns (True, "").
        """
        valido, erro = verificar_dominio(msg)
        assert valido is True
        assert erro == ""

    @given(msg=short_messages())
    @settings(max_examples=50, deadline=None)
    def test_short_messages_rejected_by_validar_mensagem(self, msg: str):
        """
        **Validates: Requirements 3.4**

        For all messages with fewer than 10 non-space characters →
        validar_mensagem rejects regardless of content.
        """
        valido, erro = validar_mensagem(msg)
        assert valido is False
        assert erro != ""


# ---------------------------------------------------------------------------
# Additional parametrized preservation tests
# ---------------------------------------------------------------------------

class TestPreservationParametrized:
    """Parametrized tests covering preservation edge cases."""

    @pytest.mark.parametrize("keyword", ORIGINAL_KEYWORDS)
    def test_each_original_keyword_accepted(self, keyword: str):
        """Each original keyword individually triggers domain acceptance."""
        msg = f"Preciso de ajuda com meu {keyword} por favor"
        valido, erro = verificar_dominio(msg)
        assert valido is True, f"Keyword '{keyword}' was not recognized"
        assert erro == ""

    @pytest.mark.parametrize("keyword", ORIGINAL_KEYWORDS)
    def test_each_keyword_case_insensitive(self, keyword: str):
        """Keywords work case-insensitively."""
        msg = f"AJUDA COM {keyword.upper()} AGORA"
        valido, erro = verificar_dominio(msg)
        assert valido is True, f"Uppercase keyword '{keyword.upper()}' was not recognized"

    @pytest.mark.parametrize("code,expected", [
        ("XYZ123", True),
        ("ABCDEF", True),
        ("123456", True),
        ("abc123", False),
        ("ABC12", False),
        ("ABC1234", False),
        ("", False),
        ("AB-123", False),
        ("ABC 12", False),
    ])
    def test_code_format_validation(self, code: str, expected: bool):
        """Code format validation remains unchanged."""
        valido, _ = validar_codigo_reserva(code)
        assert valido is expected

    @pytest.mark.parametrize("msg,expected_valid", [
        ("abcdefghij", True),          # exactly 10 non-space
        ("a" * 2000, True),            # max length
        ("", False),                    # empty
        ("   ", False),                 # only spaces
        ("abc", False),                 # too short
        ("a" * 2001, False),           # too long
        ("a b c d e", False),          # 5 non-space chars
    ])
    def test_message_size_validation(self, msg: str, expected_valid: bool):
        """Message size validation remains unchanged."""
        valido, _ = validar_mensagem(msg)
        assert valido is expected_valid

    @pytest.mark.parametrize("msg", [
        "qual a receita de bolo?",
        "como fazer arroz integral?",
        "quem ganhou o jogo ontem?",
        "qual o sentido da vida?",
        "me conta uma piada engraçada",
    ])
    def test_non_domain_messages_rejected(self, msg: str):
        """Messages completely unrelated to travel are rejected by verificar_dominio."""
        valido, erro = verificar_dominio(msg)
        assert valido is False
        assert "itinerários de viagem" in erro
