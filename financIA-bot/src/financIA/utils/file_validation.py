from enum import Enum
import pandas as pd
from pathlib import Path

class BankType(Enum):
    ITAU = 'Itaú'
    BRADESCO = 'Bradesco'
    SANTANDER = 'Santander'

def validate_bank_statement(file_path: str) -> BankType:
    """Valida e identifica o tipo de extrato bancário"""
    if not Path(file_path).exists():
        raise ValueError("Arquivo não encontrado")
    
    # Verifica extensão
    if not file_path.lower().endswith(('.csv', '.xlsx')):
        raise ValueError("Formato inválido. Use CSV ou XLSX")
    
    # Detecta o banco pelo conteúdo
    try:
        df = pd.read_csv(file_path, nrows=5)
        
        if 'Itaú' in df.columns[0]:
            return BankType.ITAU
        elif 'BRADESCO' in df.columns[0]:
            return BankType.BRADESCO
        else:
            raise ValueError("Banco não suportado")
    except Exception as e:
        raise ValueError(f"Não foi possível identificar o banco: {str(e)}")