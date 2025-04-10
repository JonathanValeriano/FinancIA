from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, MessageHandler, filters
from pathlib import Path
from datetime import datetime
import tempfile
import logging
from typing import Dict, Any
import pandas as pd

from ..core.database import DatabaseManager
from ..services.analysis_service import AnalysisService
from ..file_parsers.bank_parser import BankParserFactory
from ..utils.file_validation import validate_bank_statement
from ..config import Config

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, db: DatabaseManager, analysis: AnalysisService):
        self.db = db
        self.analysis = analysis
    
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Menu principal com todas as opções"""
        user = update.effective_user
        keyboard = [
            [InlineKeyboardButton("📊 Saldo", callback_data='balance'),
             InlineKeyboardButton("📋 Extrato", callback_data='statement')],
            [InlineKeyboardButton("🔗 Conectar Open Finance", callback_data='connect_of'),
             InlineKeyboardButton("🔄 Sincronizar", callback_data='sync_of')],
            [InlineKeyboardButton("📤 Enviar Extrato", callback_data='upload_file')]
        ]
        
        await update.message.reply_text(
            f"👋 Olá {user.first_name}! Eu sou seu assistente financeiro.\n\n"
            "Você pode:\n"
            "- Ver seu saldo e extrato\n"
            "- Conectar bancos via Open Finance\n"
            "- Enviar extratos bancários",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_balance(self, update: Update, context: CallbackContext) -> None:
        """Handler para saldo"""
        user_id = update.effective_user.id
        balance = self.db.get_balance(user_id)
        
        await update.message.reply_text(
            f"📊 Seu saldo atual é: R$ {balance:.2f}\n\n"
            f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
    
    async def handle_statement(self, update: Update, context: CallbackContext) -> None:
        """Handler para extrato"""
        user_id = update.effective_user.id
        transactions = self.db.get_last_transactions(user_id, limit=5)
        
        response = "📋 Últimas transações:\n"
        for t in transactions:
            response += f"\n• {t['date']}: {t['description']} - R$ {t['amount']:.2f} ({t['category']})"
        
        await update.message.reply_text(response)
    
    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handler para mensagens não-comando"""
        if context.user_data.get('awaiting_of_token'):
            await self.handle_open_finance_token(update, context)
        elif context.user_data.get('awaiting_file_upload'):
            await self.handle_file_upload(update, context)
        else:
            await update.message.reply_text("Por favor use os botões do menu:")
            await self.start(update, context)
    
    # --- Open Finance Handlers ---
    
    async def handle_open_finance_connect(self, update: Update, context: CallbackContext) -> None:
        """Inicia fluxo de conexão com Open Finance"""
        query = update.callback_query
        await query.answer()
        
        instructions = (
            "🔗 Para conectar seu banco via Open Finance:\n\n"
            "1. Acesse seu internet banking\n"
            "2. Procure por 'Open Finance' ou 'Compartilhamento de dados'\n"
            "3. Autorize o compartilhamento com 'FinancIA Bot'\n"
            "4. Envie-nos o código de autorização\n\n"
            "⚠️ O código é válido por apenas 5 minutos"
        )
        
        await query.edit_message_text(
            instructions,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancelar", callback_data='cancel_of')]
            ])
        )
        
        context.user_data['awaiting_of_token'] = True
    
    async def handle_cancel_of(self, update: Update, context: CallbackContext) -> None:
        """Cancela o processo de conexão com Open Finance"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "❌ Conexão com Open Finance cancelada.",
            reply_markup=None
        )
        
        context.user_data.pop('awaiting_of_token', None)
    
    async def handle_open_finance_token(self, update: Update, context: CallbackContext) -> None:
        """Processa token de autorização do Open Finance"""
        token = update.message.text.strip()
        
        try:
            account_info = self._exchange_token(token)
            self.db.save_open_finance_connection(
                user_id=update.effective_user.id,
                account_id=account_info['account_id'],
                access_token=account_info['access_token'],
                refresh_token=account_info['refresh_token']
            )
            
            await update.message.reply_text(
                "✅ Banco conectado com sucesso!\n\n"
                f"Banco: {account_info['institution']}\n"
                f"Conta: {account_info['account_number']}\n\n"
                "Agora você pode usar /sincronizar para atualizar seus dados."
            )
            
        except Exception as e:
            logger.error(f"Erro na conexão Open Finance: {str(e)}")
            await update.message.reply_text(
                f"❌ Falha na conexão: {str(e)}\n\n"
                "Por favor tente novamente ou contate o suporte."
            )
        finally:
            context.user_data.pop('awaiting_of_token', None)
    
    async def handle_open_finance_sync(self, update: Update, context: CallbackContext) -> None:
        """Sincroniza dados via Open Finance"""
        user_id = update.effective_user.id
        connection = self.db.get_of_connection(user_id)
        
        if not connection:
            await update.message.reply_text(
                "⚠️ Nenhum banco conectado.\n"
                "Use /conectar_openfinance primeiro."
            )
            return
        
        try:
            last_sync = self.db.get_last_sync_date(user_id)
            count = self.analysis.process_source(
                source_type='open_finance',
                account_id=connection['account_id'],
                start_date=last_sync or '2023-01-01',
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            self.db.update_last_sync(user_id)
            
            await update.message.reply_text(
                f"🔄 Sincronização concluída!\n"
                f"• {count} novas transações\n"
                f"• Saldo atual: R$ {self.db.get_balance(user_id):.2f}"
            )
            
        except Exception as e:
            logger.error(f"Erro na sincronização: {str(e)}")
            await update.message.reply_text(
                f"❌ Falha na sincronização: {str(e)}\n\n"
                "Tentando novamente em 5 minutos..."
            )
    
    # --- File Upload Handlers ---
    
    async def initiate_file_upload(self, update: Update, context: CallbackContext) -> None:
        """Inicia o processo de upload de arquivo"""
        query = update.callback_query
        await query.answer()
        
        instructions = (
            "📤 Envie seu extrato bancário (CSV ou Excel):\n\n"
            "1. Vá até o internet banking\n"
            "2. Exporte o extrato como CSV ou Excel\n"
            "3. Envie o arquivo aqui\n\n"
            "⚠️ Formatos suportados: .csv, .xlsx, .xls\n"
            "⚠️ Tamanho máximo: 5MB"
        )
        
        await query.edit_message_text(
            instructions,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancelar", callback_data='cancel_upload')]
            ])
        )
        
        context.user_data['awaiting_file_upload'] = True
    
    async def handle_cancel_upload(self, update: Update, context: CallbackContext) -> None:
        """Cancela o processo de upload"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "❌ Upload de arquivo cancelado.",
            reply_markup=None
        )
        
        context.user_data.pop('awaiting_file_upload', None)
    
    async def handle_file_upload(self, update: Update, context: CallbackContext) -> None:
        """Processa arquivos bancários enviados"""
        if not context.user_data.get('awaiting_file_upload'):
            await update.message.reply_text("Por favor inicie o upload usando o botão no menu.")
            return
        
        user = update.effective_user
        document = update.message.document
        
        # Verifica tamanho do arquivo (max 5MB)
        if document.file_size > 5 * 1024 * 1024:
            await update.message.reply_text("❌ Arquivo muito grande. Tamanho máximo: 5MB")
            return
        
        file_ext = Path(document.file_name).suffix.lower()
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            await update.message.reply_text("❌ Formato não suportado. Envie CSV ou Excel.")
            return
        
        try:
            # Cria diretório para uploads do usuário
            user_dir = Path(Config.UPLOADS_DIR) / str(user.id)
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Faz download do arquivo
            file_path = user_dir / f"extrato_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            file = await document.get_file()
            await file.download_to_drive(file_path)
            
            # Processa o arquivo
            bank_type = validate_bank_statement(file_path)
            transactions = self.analysis.process_file(file_path, bank_type)
            
            await update.message.reply_text(
                f"✅ Extrato processado com sucesso!\n\n"
                f"• Banco: {bank_type.value}\n"
                f"• Transações importadas: {len(transactions)}\n"
                f"• Saldo atualizado: R$ {self.db.get_balance(user.id):.2f}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Ver Extrato", callback_data='statement')]
                ])
            )
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Erro no arquivo: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Ocorreu um erro ao processar seu arquivo.")
        finally:
            context.user_data.pop('awaiting_file_upload', None)
    
    # --- Helper Methods ---
    
    def _exchange_token(self, auth_code: str) -> Dict[str, Any]:
        """Implementação real da troca de tokens OAuth2"""
        response = requests.post(
            Config.OPEN_FINANCE_TOKEN_URL,
            auth=(Config.OPEN_FINANCE_CLIENT_ID, Config.OPEN_FINANCE_CLIENT_SECRET),
            data={
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': Config.OPEN_FINANCE_REDIRECT_URI
            },
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Falha na autenticação: {response.text}")
        
        data = response.json()
        return {
            'account_id': data['account_id'],
            'account_number': data['account_number'],
            'institution': data['institution_name'],
            'access_token': data['access_token'],
            'refresh_token': data['refresh_token']
        }