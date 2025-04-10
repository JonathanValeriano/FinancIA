from enum import Enum
import pandas as pd
from abc import ABC, abstractmethod

class BankType(Enum):
    ITAU = 'Itaú'
    BRADESCO = 'Bradesco'
    SANTANDER = 'Santander'

class BankParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> list[dict]:
        pass

class ItauParser(BankParser):
    def parse(self, file_path: str) -> list[dict]:
        df = pd.read_csv(file_path, encoding='iso-8859-1')
        # Implemente a lógica específica para Itaú
        return df.to_dict('records')

class BankParserFactory:
    @staticmethod
    def get_parser(bank_type: BankType) -> BankParser:
        parsers = {
            BankType.ITAU: ItauParser(),
            BankType.BRADESCO: BradescoParser(),
            BankType.SANTANDER: SantanderParser()
        }
        return parsers[bank_type]