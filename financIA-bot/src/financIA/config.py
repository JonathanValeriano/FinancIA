import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).parent.parent
    DB_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/processed/transactions.db")
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPEN_FINANCE_CLIENT_ID = os.getenv('OPEN_FINANCE_CLIENT_ID')
    OPEN_FINANCE_CLIENT_SECRET = os.getenv('OPEN_FINANCE_CLIENT_SECRET')
    
    @classmethod
    def ensure_dirs(cls):
        """Cria diretórios necessários"""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)