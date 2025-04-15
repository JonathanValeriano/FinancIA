import pytest

@pytest.fixture
def sample_transaction():
    return {
        "descricao": "PIX MERCADO LIVRE",
        "valor": -150.00,
        "data": "2024-04-01"
    }
