import pytest
from src.financIA.core import categorizer

def test_rule_based_categorization():
    result = categorizer.categorize_transaction("PIX MERCADO LIVRE")
    assert result == "Transferência"

def test_model_fallback(monkeypatch):
    monkeypatch.setattr(categorizer, "apply_manual_rules", lambda x: None)
    result = categorizer.categorize_transaction("Compra em supermercado")
    assert isinstance(result, str)
