import pytest
from pathlib import Path
from src.financIA.utils.file_validation import validate_bank_statement, BankType

def test_file_not_found(tmp_path):
    fake_file = tmp_path / "nao_existe.csv"
    with pytest.raises(ValueError, match="Arquivo não encontrado"):
        validate_bank_statement(fake_file)

def test_invalid_extension(tmp_path):
    invalid_file = tmp_path / "extrato.txt"
    invalid_file.write_text("algum conteúdo")
    with pytest.raises(ValueError, match="Formato inválido"):
        validate_bank_statement(invalid_file)

def test_detect_itau_csv(tmp_path):
    itau_file = tmp_path / "itau.csv"
    itau_file.write_text("Itaú Agência,Valor\n1234,-50.00", encoding="latin1")
    assert validate_bank_statement(itau_file) == BankType.ITAU

def test_detect_bradesco_csv(tmp_path):
    bradesco_file = tmp_path / "bradesco.csv"
    bradesco_file.write_text("BRADESCO CONTA,Valor\n4321,-100.00", encoding="latin1")
    assert validate_bank_statement(bradesco_file) == BankType.BRADESCO

def test_detect_santander_csv(tmp_path):
    santander_file = tmp_path / "santander.csv"
    santander_file.write_text("SANTANDER CONTA,Valor\n8765,-200.00", encoding="latin1")
    assert validate_bank_statement(santander_file) == BankType.SANTANDER
    
def test_detect_nubank_real_example(tmp_path):
    file = tmp_path / "nubank.csv"
    file.write_text(
        "Data,Valor,Identificador,Descrição\n"
        "02/03/2025,0.20,uuid1,Resgate RDB\n"
        "03/03/2025,-1.12,uuid2,Compra no débito\n",
        encoding="utf-8"
    )
    assert validate_bank_statement(file) == BankType.NUBANK

def test_detect_c6_csv(tmp_path):
    c6_file = tmp_path / "c6.csv"
    c6_file.write_text("C6 BANK CONTA,Valor\n1234,-200.00", encoding="utf-8")
    assert validate_bank_statement(c6_file) == BankType.C6

def test_detect_inter_csv(tmp_path):
    inter_file = tmp_path / "inter.csv"
    inter_file.write_text("INTER CONTA,Valor\n5678,-100.00", encoding="utf-8")
    assert validate_bank_statement(inter_file) == BankType.INTER

def test_unsupported_bank_csv(tmp_path):
    unknown_file = tmp_path / "desconhecido.csv"
    unknown_file.write_text("BANCO XYZ,Valor\n0000,-75.00", encoding="latin1")
    with pytest.raises(ValueError, match="Banco não suportado"):
        validate_bank_statement(unknown_file)
