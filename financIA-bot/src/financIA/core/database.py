import sqlite3
from pathlib import Path
import logging
from src.financIA.config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerencia todas as operações do banco de dados"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Config.DB_PATH)
        self._init_db()

    def _init_db(self):
        """Cria a estrutura inicial do banco"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT,
                    user_id INTEGER
                )""")
            conn.commit()

    def _get_connection(self):
        """Retorna uma conexão com o banco (agora como gerenciador de contexto)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    def save_open_finance_connection(self, user_id: int, account_id: str, token: str):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO open_finance_connections 
                (user_id, account_id, access_token) 
                VALUES (?, ?, ?)
            ''', (user_id, account_id, token))
            conn.commit()

    def get_of_connection(self, user_id: int) -> dict:
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT account_id, access_token 
                FROM open_finance_connections 
                WHERE user_id = ?
         ''', (user_id,))
        return cursor.fetchone()