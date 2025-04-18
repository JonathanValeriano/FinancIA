from abc import ABC, abstractmethod
from typing import List, Dict
import logging
from pathlib import Path
import pandas as pd
from src.financIA.enums.bank_type import BankType


logger = logging.getLogger(__name__)

class BankParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict]:
        pass

def clean_amount(value) -> float:
    try:
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
        return float(value)
    except Exception:
        return 0.0

def load_csv(file_path: str, sep: str = ',', fallback_encoding: str = 'iso-8859-1') -> pd.DataFrame:
    try:
        return pd.read_csv(file_path, sep=sep, encoding='utf-8', engine='python')
    except UnicodeDecodeError:
        return pd.read_csv(file_path, sep=sep, encoding=fallback_encoding, engine='python')

class ItauParser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = load_csv(file_path)
            required_columns = {'Data', 'Histórico', 'Valor'}
            if not required_columns.issubset(df.columns):
                raise ValueError(f"[Itaú] Colunas esperadas: {required_columns}, encontradas: {df.columns.tolist()}")
            logger.info(f"[Itaú] Colunas detectadas: {df.columns.tolist()}")
            return [
                {
                    'date': row['Data'],
                    'description': row['Histórico'],
                    'amount': clean_amount(row['Valor']),
                    'bank_type': 'itau'
                } for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"[Itaú] Erro ao parsear arquivo: {str(e)}")
            raise

class BradescoParser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            required_columns = {'Data', 'Descrição', 'Valor'}
            if not required_columns.issubset(df.columns):
                raise ValueError(f"[Bradesco] Colunas esperadas: {required_columns}, encontradas: {df.columns.tolist()}")
            logger.info(f"[Bradesco] Colunas detectadas: {df.columns.tolist()}")
            return [
                {
                    'date': row['Data'],
                    'description': row['Descrição'],
                    'amount': clean_amount(row['Valor']),
                    'bank_type': 'bradesco'
                } for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"[Bradesco] Erro ao parsear arquivo: {str(e)}")
            raise

class SantanderParser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = load_csv(file_path, sep=';')
            required_columns = {'Data Operação', 'Descrição', 'Valor'}
            if not required_columns.issubset(df.columns):
                raise ValueError(f"[Santander] Colunas esperadas: {required_columns}, encontradas: {df.columns.tolist()}")
            logger.info(f"[Santander] Colunas detectadas: {df.columns.tolist()}")
            return [
                {
                    'date': row['Data Operação'],
                    'description': row['Descrição'],
                    'amount': clean_amount(row['Valor']),
                    'bank_type': 'santander'
                } for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"[Santander] Erro ao parsear arquivo: {str(e)}")
            raise

class NubankParser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        for sep in [';', ',']:
            try:
                df = load_csv(file_path, sep=sep)
                required_columns = {'Data', 'Descrição', 'Valor'}
                if required_columns.issubset(set(df.columns)):
                    logger.info(f"[Nubank] Colunas detectadas com sep='{sep}': {df.columns.tolist()}")
                    return [
                        {
                            'date': row['Data'],
                            'description': row['Descrição'],
                            'amount': clean_amount(row['Valor']),
                            'bank_type': 'nubank'
                        } for _, row in df.iterrows()
                    ]
            except Exception as e:
                logger.warning(f"[Nubank] Tentativa com separador '{sep}' falhou: {e}")
        
        raise ValueError(f"[Nubank] Colunas esperadas: {{'Valor', 'Descrição', 'Data'}}, mas não foram encontradas.")


class C6Parser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = load_csv(file_path, sep=';')
            required_columns = {'Data', 'Descrição', 'Valor'}
            if not required_columns.issubset(df.columns):
                raise ValueError(f"[C6] Colunas esperadas: {required_columns}, encontradas: {df.columns.tolist()}")
            logger.info(f"[C6] Colunas detectadas: {df.columns.tolist()}")
            return [
                {
                    'date': row.get('Data', ''),
                    'description': row.get('Descrição', ''),
                    'amount': clean_amount(row.get('Valor', 0)),
                    'bank_type': 'c6'
                } for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"[C6 Bank] Erro ao parsear arquivo: {str(e)}")
            raise

class InterParser(BankParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = load_csv(file_path, sep=';')
            required_columns = {'Data', 'Descrição', 'Valor'}
            if not required_columns.issubset(df.columns):
                raise ValueError(f"[Inter] Colunas esperadas: {required_columns}, encontradas: {df.columns.tolist()}")
            logger.info(f"[Inter] Colunas detectadas: {df.columns.tolist()}")
            return [
                {
                    'date': row.get('Data', ''),
                    'description': row.get('Descrição', ''),
                    'amount': clean_amount(row.get('Valor', 0)),
                    'bank_type': 'inter'
                } for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"[Banco Inter] Erro ao parsear arquivo: {str(e)}")
            raise

class BankParserFactory:
    @staticmethod
    def get_parser(bank_type: BankType) -> BankParser:
        logger.debug(f"[DEBUG] Tipo de banco recebido: {bank_type} ({type(bank_type)})")

        if isinstance(bank_type, str):
            try:
                bank_type = BankType(bank_type)
            except ValueError:
                raise ValueError(f"Tipo de banco desconhecido (string): {bank_type}")

        parsers = {
            BankType.ITAU: ItauParser(),
            BankType.BRADESCO: BradescoParser(),
            BankType.SANTANDER: SantanderParser(),
            BankType.NUBANK: NubankParser(),
            BankType.C6: C6Parser(),
            BankType.INTER: InterParser()
        }
        parser = parsers.get(bank_type)
        if not parser:
            raise ValueError(f"Parser não disponível para o banco: {bank_type}")
        return parser
