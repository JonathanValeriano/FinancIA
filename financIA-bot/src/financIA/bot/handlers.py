from telegram import Update
from telegram.ext import CallbackContext
from src.financIA.core.database import DatabaseManager
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

class BotHandlers:
    def __init__(self, db: DatabaseManager):
        self.db = db

async def handle_message(self, update: Update, context: CallbackContext):
    """Lida com mensagens não-comando"""
    await update.message.reply_text(
        "🤖 Eu sou um bot financeiro. Use os comandos:\n"
        "/start - Menu principal\n"
        "/saldo - Ver seu saldo\n"
        "/extrato - Ver transações"
    )

    async def handle_balance(self, update: Update, context: CallbackContext):
        with self.db._get_connection() as conn:
            saldo = conn.execute("SELECT SUM(amount) FROM transactions").fetchone()[0] or 0
        await update.message.reply_text(f"💰 Saldo atual: R$ {saldo:.2f}")

    async def handle_statement(self, update: Update, context: CallbackContext):
        with self.db._get_connection() as conn:
            transacoes = conn.execute(
                "SELECT date, description, amount FROM transactions ORDER BY date DESC LIMIT 10"
            ).fetchall()
        
        if not transacoes:
            await update.message.reply_text("📭 Nenhuma transação encontrada")
            return

        resposta = "📋 Últimas transações:\n"
        for t in transacoes:
            resposta += f"\n📅 {t['date']} | {t['description'][:20]}... | R$ {t['amount']:.2f}"
        
        await update.message.reply_text(resposta)