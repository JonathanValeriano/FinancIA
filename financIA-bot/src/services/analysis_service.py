from ..integrations.open_finance import OpenFinanceIntegration
from src.financIA.core.categorizer import SmartCategorizer
from typing import Union, List, Dict  # Importação consolidada

class AnalysisService:
    def __init__(self, db_manager, of_client: Union[OpenFinanceIntegration, None] = None):
        self.db = db_manager
        self.of_client = of_client
        self.categorizer = SmartCategorizer('bert_model')
    
    def process_source(self, source_type: str, **kwargs):
        """
        Processa dados de qualquer fonte
        Args:
            source_type: 'open_finance' ou 'file'
            kwargs:
                - Para Open Finance: account_id, start_date, end_date
                - Para arquivos: file_path, bank_type
        """
        if source_type == 'open_finance' and self.of_client:
            transactions = self.of_client.get_transactions(
                kwargs['account_id'],
                kwargs['start_date'],
                kwargs['end_date']
            )
        else:
            transactions = self._parse_file(
                kwargs['file_path'],
                kwargs['bank_type']
            )
        
        return self._process_transactions(transactions)

    def _process_transactions(self, transactions: List[Dict]) -> int:
        """Processamento comum para todas as fontes"""
        categorized = []
        for t in transactions:
            t['category'] = self.categorizer.categorize(
                t['description'],
                t.get('bank_type')
            )
            categorized.append(t)
        
        self.db.save_transactions(categorized)
        return len(categorized)