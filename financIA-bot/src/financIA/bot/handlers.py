from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any
import pandas as pd
import requests

from ..utils.asset_validation import validate_asset_symbol
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

    async def send_error_message(self, update: Update, message: str) -> None:
        if update.callback_query:
            await update.callback_query.message.reply_text(f"❌ {message}")
        elif update.message:
            await update.message.reply_text(f"❌ {message}")

    async def start(self, update: Update, context: CallbackContext) -> None:
        try:
            user = update.effective_user
            keyboard = [
                [InlineKeyboardButton("📊 Saldo", callback_data='balance'),
                 InlineKeyboardButton("📋 Extrato", callback_data='statement')],
                [InlineKeyboardButton("🔗 Conectar Open Finance", callback_data='connect_of'),
                 InlineKeyboardButton("🔄 Sincronizar", callback_data='sync_of')],
                [InlineKeyboardButton("📤 Enviar Extrato", callback_data='upload_file')],
                [InlineKeyboardButton("➕ Incluir Ativo", callback_data='add_asset'),
                 InlineKeyboardButton("📈 Ver Meus Ativos", callback_data='list_assets')]
            ]

            await update.message.reply_text(
                f"👋 Olá {user.first_name}! Eu sou seu assistente financeiro.\n\n"
                "Você pode:\n"
                "- Ver seu saldo e extrato\n"
                "- Conectar bancos via Open Finance\n"
                "- Enviar extratos bancários\n"
                "- Incluir e visualizar seus ativos (ações, FIIs, etc.)",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Erro no comando start: {str(e)}", exc_info=True)
            await self.send_error_message(update, "Erro ao exibir menu principal")

    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        if context.user_data.get('awaiting_of_token'):
            await self.handle_open_finance_token(update, context)
        elif context.user_data.get('awaiting_file_upload'):
            await self.handle_file_upload(update, context)
        elif context.user_data.get('awaiting_asset_input'):
            await self.handle_asset_input(update, context)
        else:
            await update.message.reply_text("Por favor use os botões do menu:")
            await self.start(update, context)

    async def handle_add_asset(self, update: Update, context: CallbackContext) -> None:
        try:
            if update.callback_query:
                query = update.callback_query
                await query.answer()
                chat_id = query.message.chat_id
                message_id = query.message.message_id
            else:
                chat_id = update.message.chat_id
                message_id = None

            context.user_data['awaiting_asset_input'] = True
            context.user_data['asset_message_id'] = message_id

            keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data='cancel_add_asset')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            text = "📝 Digite o nome do ativo que deseja adicionar (ex: PETR4, KNRI11):"

            if update.callback_query:
                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text, reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Erro em handle_add_asset: {str(e)}", exc_info=True)
            await self.send_error_message(update, "Ocorreu um erro ao iniciar a adição de ativo.")

    async def handle_asset_input(self, update: Update, context: CallbackContext) -> None:
        try:
            if not context.user_data.get('awaiting_asset_input'):
                return

            user_id = update.effective_user.id
            asset_name = update.message.text.strip().upper()
            
            logger.info(f"[BOT] Usuário {user_id} enviou ativo: {asset_name}")

            if not asset_name:
                await update.message.reply_text("⚠️ O nome do ativo não pode estar vazio. Tente novamente.")
                return

            if not validate_asset_symbol(asset_name):
                logger.warning(f"[VALIDAÇÃO] Ativo '{asset_name}' foi rejeitado pela API")
                await update.message.reply_text(
                    "❌ Não foi possível validar o ativo agora. "
                    "Verifique o nome (ex: PETR4, MXRF11) ou tente novamente mais tarde."
                )
                return

            self.db.save_asset_name_only(user_id=user_id, asset_name=asset_name)
            context.user_data.pop('awaiting_asset_input', None)

            keyboard = [
                [InlineKeyboardButton("📈 Ver Meus Ativos", callback_data='list_assets')],
                [InlineKeyboardButton("➕ Adicionar Outro", callback_data='add_asset')]
            ]

            await update.message.reply_text(
                f"✅ Ativo '{asset_name}' adicionado com sucesso!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            if 'asset_message_id' in context.user_data:
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['asset_message_id'])
                except Exception as e:
                    logger.warning(f"Erro ao deletar mensagem de entrada: {str(e)}")
                finally:
                    context.user_data.pop('asset_message_id', None)

        except Exception as e:
            logger.error(f"Erro ao salvar ativo: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Falha ao adicionar ativo. Por favor, tente novamente.")

    async def handle_cancel_add_asset(self, update: Update, context: CallbackContext) -> None:
        try:
            query = update.callback_query
            await query.answer()

            context.user_data.pop('awaiting_asset_input', None)
            context.user_data.pop('asset_message_id', None)

            await query.edit_message_text(
                "❌ Adição de ativo cancelada.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Menu Principal", callback_data='main_menu')]
                ])
            )

        except Exception as e:
            logger.error(f"Erro ao cancelar adição de ativo: {str(e)}", exc_info=True)
            await self.send_error_message(update, "Ocorreu um erro ao cancelar a adição.")

    async def handle_asset_list(self, update: Update, context: CallbackContext) -> None:
        user_id = update.effective_user.id
        assets = self.db.get_user_assets(user_id)

        if not assets:
            await update.callback_query.edit_message_text(
                "📭 Você ainda não adicionou nenhum ativo.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Adicionar ativo", callback_data="add_asset")],
                    [InlineKeyboardButton("🔙 Voltar", callback_data="back_to_menu")]
                ])
            )
            return

        keyboard = []
        for asset in assets:
            keyboard.append([
                InlineKeyboardButton(f"🗑️ {asset['name']}", callback_data=f"delete_asset:{asset['name']}")
            ])

        keyboard.append([InlineKeyboardButton("➕ Adicionar outro", callback_data='add_asset')])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')])

        await update.callback_query.edit_message_text(
            "📈 Seus ativos cadastrados:\nClique para excluir:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_delete_asset(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        asset_name = query.data.split(":")[1]

        self.db.delete_asset(user_id, asset_name)

        await query.edit_message_text(
            f"🗑️ Ativo '{asset_name}' removido com sucesso.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Atualizar lista", callback_data="list_assets")],
                [InlineKeyboardButton("➕ Adicionar ativo", callback_data="add_asset")]
            ])
        )
        
    async def handle_balance(self, update: Update, context: CallbackContext) -> None:
        try:
            user_id = update.effective_user.id
            balance = self.db.get_balance(user_id)  # Supondo que o método get_balance exista no seu DB

            if balance is None:
                await update.message.reply_text("⚠️ Não foi possível recuperar o saldo.")
                return

            await update.message.reply_text(
                f"💰 Seu saldo atual é: R$ {balance:.2f}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Atualizar", callback_data='sync_balance')],
                    [InlineKeyboardButton("📋 Ver Extrato", callback_data='statement')]
                ])
            )
        except Exception as e:
            logger.error(f"Erro ao obter saldo: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Ocorreu um erro ao obter o saldo. Tente novamente mais tarde.")
    async def handle_statement(self, update: Update, context: CallbackContext) -> None:
        try:
            user_id = update.effective_user.id
            statement = self.db.get_statement(user_id)  # Supondo que o método get_statement exista no seu DB

            if not statement:
                await update.message.reply_text("⚠️ Não foi possível recuperar o extrato.")
                return

            # Exemplo de como exibir o extrato
            response = "📋 Seu extrato bancário:\n\n"
            for transaction in statement:
                response += f"• {transaction['description']} - R$ {transaction['amount']:.2f}\n"

            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Erro ao obter extrato: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Ocorreu um erro ao obter seu extrato. Tente novamente mais tarde.")


    # --- Open Finance Handlers ---

    async def handle_open_finance_connect(self, update: Update, context: CallbackContext) -> None:
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
        query = update.callback_query
        await query.answer()

        await query.edit_message_text("❌ Conexão com Open Finance cancelada.", reply_markup=None)
        context.user_data.pop('awaiting_of_token', None)

    async def handle_open_finance_token(self, update: Update, context: CallbackContext) -> None:
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
                f"❌ Falha na conexão: {str(e)}\n\nPor favor tente novamente ou contate o suporte."
            )
        finally:
            context.user_data.pop('awaiting_of_token', None)

    async def handle_open_finance_sync(self, update: Update, context: CallbackContext) -> None:
        user_id = update.effective_user.id
        connection = self.db.get_of_connection(user_id)

        if not connection:
            await update.message.reply_text("⚠️ Nenhum banco conectado. Use /conectar_openfinance primeiro.")
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
                f"🔄 Sincronização concluída!\n• {count} novas transações\n• Saldo atual: R$ {self.db.get_balance(user_id):.2f}"
            )

        except Exception as e:
            logger.error(f"Erro na sincronização: {str(e)}")
            await update.message.reply_text(
                f"❌ Falha na sincronização: {str(e)}\n\nTentando novamente em 5 minutos..."
            )

    # --- File Upload Handlers ---

    async def initiate_file_upload(self, update: Update, context: CallbackContext) -> None:
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
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Upload de arquivo cancelado.", reply_markup=None)
        context.user_data.pop('awaiting_file_upload', None)

    async def handle_file_upload(self, update: Update, context: CallbackContext) -> None:
        if not context.user_data.get('awaiting_file_upload'):
            await update.message.reply_text("Por favor inicie o upload usando o botão no menu.")
            return

        user = update.effective_user
        document = update.message.document

        if document.file_size > 5 * 1024 * 1024:
            await update.message.reply_text("❌ Arquivo muito grande. Tamanho máximo: 5MB")
            return

        file_ext = Path(document.file_name).suffix.lower()
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            await update.message.reply_text("❌ Formato não suportado. Envie CSV ou Excel.")
            return

        try:
            user_dir = Path(Config.UPLOADS_DIR) / str(user.id)
            user_dir.mkdir(parents=True, exist_ok=True)
            file_path = user_dir / f"extrato_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            file = await document.get_file()
            await file.download_to_drive(file_path)
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