from ..integrations.open_finance import OpenFinanceIntegration
from ..core.categorizer import SmartCategorizer
from ..file_parsers.bank_parser import BankParserFactory
from typing import Union, List, Dict
from src.financIA.file_parsers.bank_parser import BankType
import logging

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, db_manager, of_client: Union[OpenFinanceIntegration, None] = None):
        self.db = db_manager
        self.of_client = of_client
        self.categorizer = SmartCategorizer('bert_model')

    def process_file(self, file_path: str, bank_type: BankType) -> List[Dict]:
        """
        Processa um arquivo de extrato bancário.
        """
        try:
            logger.debug(f"[DEBUG] Tipo de banco recebido: {bank_type} ({type(bank_type)})")
            parser = BankParserFactory.get_parser(bank_type)
            transactions = parser.parse(file_path)
            logger.info(f"[DEBUG] Tipo de banco recebido: {bank_type} ({type(bank_type)})")
            logger.info(f"Tipo detectado: {bank_type} ({type(bank_type)})")
            logger.info(f"{len(transactions)} transações extraídas de {bank_type.value}")
            self._process_transactions(transactions)
            return transactions
        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {e}")
            raise

    def _process_transactions(self, transactions: List[Dict]) -> int:
        """
        Categoriza transações e retorna o total processado.
        """
        for t in transactions:
            t['category'] = self.categorizer.categorize(t['description'])
        return len(transactions)
