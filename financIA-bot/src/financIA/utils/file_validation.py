import pandas as pd
from pathlib import Path
from src.financIA.enums.bank_type import BankType


def validate_bank_statement(file_path: Path) -> BankType:
    file_path = Path(file_path)

    if not file_path.exists():
        raise ValueError("Arquivo não encontrado")

    if file_path.suffix.lower() not in ['.csv', '.xlsx']:
        raise ValueError("Formato inválido. Use CSV ou XLSX")

    try:
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path, nrows=5, encoding='utf-8', sep=None, engine='python')
        else:
            df = pd.read_excel(file_path, nrows=5)

        cols = set(df.columns)

        # Detecção por colunas específicas
        if 'Itaú' in df.columns[0] or 'ITAU' in df.columns[0].upper():
            return BankType.ITAU
        elif 'BRADESCO' in df.columns[0].upper():
            return BankType.BRADESCO
        elif 'SANTANDER' in df.columns[0].upper():
            return BankType.SANTANDER
        elif {'Data', 'Valor', 'Descrição'}.issubset(cols):
            return BankType.NUBANK
        elif any('C6' in col.upper() for col in df.columns):
            return BankType.C6
        elif any('INTER' in col.upper() for col in df.columns):
            return BankType.INTER
        else:
            raise ValueError("Banco não suportado ou não identificado")

    except Exception as e:
        raise ValueError(f"Não foi possível identificar o banco: {str(e)}")
