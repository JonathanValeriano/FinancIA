from ..file_parsers.bank_parser import BankParserFactory, BankType
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class AnalysisService:
    def process_file(self, file_path: str, bank_type: BankType) -> List[Dict]:
        """
        Processa um extrato bancário usando o parser correspondente.
        """
        try:
            parser = BankParserFactory.get_parser(bank_type)
            transactions = parser.parse(file_path)
            logger.info(f"{len(transactions)} transações extraídas de {bank_type.value}")
            return transactions
        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {e}")
            raise
