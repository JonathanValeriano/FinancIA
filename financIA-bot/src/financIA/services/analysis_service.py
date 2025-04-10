from ..integrations.open_finance import OpenFinanceIntegration
from ..core.categorizer import SmartCategorizer
from typing import Union, List, Dict

class AnalysisService:
    def __init__(self, db_manager, of_client: Union[OpenFinanceIntegration, None] = None):
        self.db = db_manager
        self.of_client = of_client
        self.categorizer = SmartCategorizer('bert_model')
    
    def _process_transactions(self, transactions: List[Dict]) -> int:
        categorized = []
        for t in transactions:
            t['category'] = self.categorizer.categorize(t['description'])
            categorized.append(t)
        return len(categorized)