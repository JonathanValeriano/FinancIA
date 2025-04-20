import sqlite3
from pathlib import Path
import logging
from typing import List, Dict
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

            conn.execute("""
                CREATE TABLE IF NOT EXISTS open_finance_connections (
                    user_id INTEGER PRIMARY KEY,
                    account_id TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    last_sync TEXT
                )""")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    quantity REAL DEFAULT 0,
                    average_price REAL DEFAULT 0
                )""")

            conn.commit()

    def _get_connection(self):
        """Retorna uma conexão com o banco (agora como gerenciador de contexto)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --- Open Finance ---
    def save_open_finance_connection(self, user_id: int, account_id: str, access_token: str, refresh_token: str):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO open_finance_connections 
                (user_id, account_id, access_token, refresh_token) 
                VALUES (?, ?, ?, ?)
            ''', (user_id, account_id, access_token, refresh_token))
            conn.commit()

    def get_of_connection(self, user_id: int) -> dict:
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT account_id, access_token, refresh_token 
                FROM open_finance_connections 
                WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def update_last_sync(self, user_id: int):
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE open_finance_connections
                SET last_sync = ?
                WHERE user_id = ?
            ''', (now, user_id))
            conn.commit()

    def get_last_sync_date(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT last_sync FROM open_finance_connections
                WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            return row['last_sync'] if row else None

    # --- Ativos ---
    def save_asset(self, user_id: int, asset_name: str, quantity: float, average_price: float):
        with self._get_connection() as conn:
            # Verifica se o ativo já existe
            cursor = conn.execute('''
                SELECT quantity, average_price FROM assets
                WHERE user_id = ? AND name = ?
            ''', (user_id, asset_name))
            row = cursor.fetchone()

            if row:
                # Se já existir, atualiza quantidade e calcula novo preço médio
                old_quantity = row['quantity']
                old_avg_price = row['average_price']
                new_quantity = old_quantity + quantity

                if new_quantity == 0:
                    new_avg_price = 0
                else:
                    new_avg_price = ((old_quantity * old_avg_price) + (quantity * average_price)) / new_quantity

                conn.execute('''
                    UPDATE assets
                    SET quantity = ?, average_price = ?
                    WHERE user_id = ? AND name = ?
                ''', (new_quantity, new_avg_price, user_id, asset_name))
            else:
                # Caso contrário, insere novo ativo
                conn.execute('''
                    INSERT INTO assets (user_id, name, quantity, average_price)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, asset_name, quantity, average_price))

            conn.commit()

    def save_asset_name_only(self, user_id: int, asset_name: str):
        try:
            logger.info(f"[DB] Salvando ativo: user_id={user_id}, asset={asset_name}")
            with self._get_connection() as conn:
                conn.execute('''
                    INSERT INTO assets (user_id, name, quantity, average_price)
                    VALUES (?, ?, 0, 0)
                ''', (user_id, asset_name))
                conn.commit()
        except Exception as e:
            logger.error(f"[DB] Erro ao salvar ativo: {e}")
            raise


    def get_user_assets(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT name, quantity, average_price
                FROM assets
                WHERE user_id = ?
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    def delete_asset(self, user_id: int, asset_name: str):
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    DELETE FROM assets
                    WHERE user_id = ? AND name = ?
                ''', (user_id, asset_name))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao deletar ativo {asset_name} do usuário {user_id}: {e}")
            raise
        
    def get_balance(self, user_id: int) -> float:
        """
        Calcula o saldo total baseado nas transações do usuário.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT SUM(amount) FROM transactions WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0.0
    def get_statement(self, user_id: int, limit: int = 10) -> list[dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, description, amount, bank_type
                FROM transactions
                WHERE user_id = ?
                ORDER BY date DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    def save_transaction(self, user_id: int, date: str, description: str, amount: float, category: str, bank_type: str):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO transactions (date, description, amount, category, user_id)
                VALUES (?, ?, ?, ?, ?)
            """, (date, description, amount, category, user_id))
            conn.commit()
            
    def get_last_transactions(self, user_id: int, limit: int = 5) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, description, amount, category
                FROM transactions
                WHERE user_id = ?
                ORDER BY date DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
