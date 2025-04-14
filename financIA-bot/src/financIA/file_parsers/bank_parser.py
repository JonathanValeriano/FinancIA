from enum import Enum
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class BankType(Enum):
    ITAU = 'itau'
    BRADESCO = 'bradesco'
    SANTANDER = 'santander'

class BankParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict]:
        pass

class ItauParser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = pd.read_csv(file_path, encoding='iso-8859-1')
            
            # Mapeamento de colunas padrão Itaú
            transactions = []
            for _, row in df.iterrows():
                transactions.append({
                    'date': row['Data'],
                    'description': row['Histórico'],
                    'amount': float(row['Valor'].replace('.', '').replace(',', '.')),
                    'bank_type': 'itau'
                })
            return transactions
            
        except Exception as e:
            logger.error(f"Erro ao parsear arquivo Itaú: {str(e)}")
            raise

class BradescoParser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = pd.read_excel(file_path)  # Bradesco geralmente usa Excel
            
            transactions = []
            for _, row in df.iterrows():
                transactions.append({
                    'date': row['Data'],
                    'description': row['Descrição'],
                    'amount': float(row['Valor']),
                    'bank_type': 'bradesco'
                })
            return transactions
            
        except Exception as e:
            logger.error(f"Erro ao parsear arquivo Bradesco: {str(e)}")
            raise

class SantanderParser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            
            transactions = []
            for _, row in df.iterrows():
                transactions.append({
                    'date': row['Data Operação'],
                    'description': row['Descrição'],
                    'amount': float(row['Valor'].replace(',', '.')),
                    'bank_type': 'santander'
                })
            return transactions
            
        except Exception as e:
            logger.error(f"Erro ao parsear arquivo Santander: {str(e)}")
            raise

class BankParserFactory:
    @staticmethod
    def get_parser(bank_type: BankType) -> BankParser:
        parsers = {
            BankType.ITAU: ItauParser(),
            BankType.BRADESCO: BradescoParser(),
            BankType.SANTANDER: SantanderParser()
        }
        return parsers[bank_type]