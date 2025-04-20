from typing import Union, List, Dict
import logging
import requests

from ..integrations.open_finance import OpenFinanceIntegration
from ..core.categorizer import SmartCategorizer
from ..file_parsers.bank_parser import BankParserFactory
from src.financIA.file_parsers.bank_parser import BankType
from ..config import Config

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, db_manager, of_client: Union[OpenFinanceIntegration, None] = None):
        self.db = db_manager
        self.of_client = of_client
        self.config = Config  # ✅ Adicionado para acessar API Key
        self.categorizer = SmartCategorizer('bert_model')

    def process_file(self, file_path: str, bank_type: BankType, user_id: int) -> List[Dict]:
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
            for tx in transactions:
                self.db.save_transaction(
                    user_id=user_id,
                    date=tx['date'],
                    description=tx['description'],
                    amount=tx['amount'],
                    category=tx.get('category', ''),
                    bank_type=tx.get('bank_type', '')
                )

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

    def get_news_summary(self, ticker: str) -> str:
        """
        Busca notícias recentes sobre o ativo usando a API NewsData.io e retorna um resumo.
        """
        try:
            url = f"https://newsdata.io/api/1/news?apikey={self.config.NEWS_API_KEY}&q={ticker}&language=pt"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            articles = data.get("results", [])[:3]
            if not articles:
                return "🔎 Nenhuma notícia encontrada."

            summary = ""
            for article in articles:
                title = article.get("title", "Sem título")
                date = article.get("pubDate", "")[:10]
                summary += f"• {title} ({date})\n"

            return summary
        except Exception as e:
            logger.warning(f"[NOTÍCIAS] Falha ao buscar para {ticker}: {e}")
            return "⚠️ Não foi possível obter notícias no momento."
