from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any
import pandas as pd
import requests
from src.financIA.utils.market_data import (
    get_stock_price,
    get_stock_indicators,
    get_latest_news,
    gerar_recomendacao,
    resumo_dos_ativos
)


from  src.financIA.enums.bank_type import BankType
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
                [InlineKeyboardButton("💸 Controle Financeiro", callback_data='controle_menu')],
                [InlineKeyboardButton("📈 Investimentos", callback_data='investimentos_menu')]
            ]
            text = (
                f"👋 Olá {user.first_name}! Eu sou seu assistente financeiro.\n\n"
                "Escolha abaixo o que deseja acessar:"
            )

            if update.message:
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            elif update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Erro no comando start: {str(e)}", exc_info=True)
            await self.send_error_message(update, "Erro ao exibir menu principal.")


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
            user_input = update.message.text.strip().upper()

            # ✅ Corrige e padroniza o nome do ativo (ex: PETR4 ➝ PETR4.SA)
            if not user_input.endswith(".SA"):
                user_input += ".SA"

            logger.info(f"[BOT] Usuário {user_id} enviou ativo: {user_input}")

            if not user_input:
                await update.message.reply_text("⚠️ O nome do ativo não pode estar vazio. Tente novamente.")
                return

            # ✅ Valida o nome com base no nome padronizado
            from src.financIA.utils.asset_validation import validate_asset_symbol
            if not validate_asset_symbol(user_input):
                logger.warning(f"[VALIDAÇÃO] Ativo '{user_input}' foi rejeitado pela API")
                await update.message.reply_text(
                    "❌ Não foi possível validar o ativo agora. "
                    "Verifique o nome (ex: PETR4, MXRF11) ou tente novamente mais tarde."
                )
                return

            # ✅ Salva o nome padronizado no banco
            self.db.save_asset_name_only(user_id=user_id, asset_name=user_input)
            context.user_data.pop('awaiting_asset_input', None)

            keyboard = [
                [InlineKeyboardButton("📈 Ver Meus Ativos", callback_data='list_assets')],
                [InlineKeyboardButton("➕ Adicionar Outro", callback_data='add_asset')]
            ]

            await update.message.reply_text(
                f"✅ Ativo '{user_input}' adicionado com sucesso!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            if 'asset_message_id' in context.user_data:
                try:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=context.user_data['asset_message_id']
                    )
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
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        try:
            assets = self.db.get_user_assets(user_id)
            if not assets:
                await query.edit_message_text("📭 Você ainda não adicionou nenhum ativo.")
                return

            manter, observar, vender = 0, 0, 0
            response = "📈 Seus ativos acompanhados:\n\n"

            for asset in assets:
                symbol = asset['name']
                indicadores = get_stock_indicators(symbol)
                noticia = get_latest_news(symbol)
                recomendacao = gerar_recomendacao(symbol, indicadores)

                preco_cota = indicadores.get("Preço", "N/A")

                if recomendacao == "✅ Manter":
                    manter += 1
                elif recomendacao == "⚠️ Observar":
                    observar += 1
                elif recomendacao == "🛑 Vender":
                    vender += 1

                response += (
                    f"📊 {symbol}\n"
                    f"├ 💹 Indicadores:\n"
                    f"│   • Preço: R$ {preco_cota}\n"
                    f"│   • P/L: {indicadores['P/L']}\n"
                    f"│   • DY: {indicadores['DY']}\n"
                    f"│   • ROE: {indicadores['ROE']}\n"
                    f"├ 📈 Recomendação: {recomendacao}\n\n"
                    f"└ 📰 Última notícia: \n{noticia}\n\n"
                )

            response += (
                f"\n📌 Resumo geral:\n"
                f"Sua carteira possui {len(assets)} ativos.\n"
                f"Recomendações:\n ✅ Manter: {manter}\n ⚠️ Observar: {observar}\n 🛑 Vender: {vender}."
            )

            keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data='back_to_investments')]]

            await query.edit_message_text(
                text=response,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro ao listar ativos: {str(e)}", exc_info=True)
            await query.edit_message_text("❌ Ocorreu um erro ao listar seus ativos.")

                
    async def handle_investimentos_menu(self, update: Update, context: CallbackContext) -> None:
        try:
            if update.callback_query:
                await update.callback_query.answer()
                keyboard = [
                    [InlineKeyboardButton("➕ Incluir Ativo", callback_data='add_asset')],
                    [InlineKeyboardButton("📈 Ver Meus Ativos", callback_data='list_assets')],
                    [InlineKeyboardButton("🗑️ Remover ativo", callback_data="remove_asset_menu")],
                    # [InlineKeyboardButton("📢 Acompanhar meus investimentos", callback_data='track_investments')],
                    [InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')]
                ]
                await update.callback_query.edit_message_text("📈 Menu de Investimentos:", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Erro ao abrir menu de investimentos: {str(e)}", exc_info=True)
            await self.send_error_message(update, "Erro ao abrir o menu de investimentos.")

    async def handle_controle_menu(self, update: Update, context: CallbackContext) -> None:
        try:
            if update.callback_query:
                await update.callback_query.answer()
                keyboard = [
                    [InlineKeyboardButton("📊 Saldo", callback_data='balance')],
                    [InlineKeyboardButton("📋 Extrato", callback_data='statement')],
                    [InlineKeyboardButton("📤 Enviar Extrato", callback_data='upload_file')],
                    [InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')]
                ]
                await update.callback_query.edit_message_text("💸 Menu de Controle Financeiro:", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Erro ao abrir menu de controle financeiro: {str(e)}", exc_info=True)
            await self.send_error_message(update, "Erro ao abrir o menu de controle financeiro.")

    async def handle_acompanhar_ativos(self, update: Update, context: CallbackContext) -> None:
        try:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text("📊 Resumo dos ativos ainda está em desenvolvimento.\nAguarde novidades!", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Voltar", callback_data='investimentos_menu')]
            ]))
        except Exception as e:
            logger.error(f"Erro em acompanhar ativos: {str(e)}", exc_info=True)
            await self.send_error_message(update, "Erro ao abrir acompanhamento de ativos.")
        async def handle_track_investments(self, update: Update, context: CallbackContext) -> None:
            query = update.callback_query
            await query.answer()

        user_id = update.effective_user.id
        assets = self.db.get_user_assets(user_id)

        if not assets:
            await query.edit_message_text("❌ Você ainda não cadastrou ativos.")
            return

        tickers = [asset['name'] for asset in assets]
        await query.edit_message_text("🔍 Buscando notícias sobre seus ativos...")

        summaries = []
        for ticker in tickers:
            resumo = self.analysis.get_news_summary(ticker)
            summaries.append(f"*📈 {ticker}*\n{resumo}")

        response = "\n\n".join(summaries)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=response,
            parse_mode='Markdown'
        )
        
    async def handle_list_assets_for_removal(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        try:
            assets = self.db.get_user_assets(user_id)
            if not assets:
                await query.edit_message_text("📭 Você ainda não adicionou nenhum ativo.")
                return

            keyboard = []
            for asset in assets:
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ Remover {asset['name']}", callback_data=f"remove_asset:{asset['name']}"
                    )
                ])

            keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data='back_to_investments')])

            await query.edit_message_text(
                "🗑️ Selecione um ativo para remover:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            logger.error(f"Erro ao listar ativos para remoção: {str(e)}", exc_info=True)
            await query.edit_message_text("❌ Ocorreu um erro ao listar os ativos.")

        
    async def handle_remove_asset(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        await query.answer()

        try:
            data = query.data
            asset_name = data.split(":")[1].upper()
            user_id = query.from_user.id

            self.db.delete_user_asset(user_id, asset_name)

            await query.edit_message_text(
                f"✅ O ativo '{asset_name}' foi removido com sucesso.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Ver Meus Ativos", callback_data='list_assets')],
                    [InlineKeyboardButton("🗑️ Remover Outro", callback_data='remove_asset_menu')],
                    [InlineKeyboardButton("🔙 Voltar", callback_data='back_to_investments')],
                ])
            )
        except Exception as e:
            logger.error(f"Erro ao remover ativo: {str(e)}", exc_info=True)
            await query.edit_message_text("❌ Ocorreu um erro ao remover o ativo.")

    async def handle_back_to_investments(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("➕ Incluir Ativo", callback_data='add_asset')],
            [InlineKeyboardButton("📈 Acompanhar Meus Ativos", callback_data='list_assets')],
            [InlineKeyboardButton("🗑️ Remover Ativo", callback_data='remove_asset_menu')],
            # [InlineKeyboardButton("📊 Resumo dos Meus Ativos", callback_data='asset_summary')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')]
        ]

        await query.edit_message_text(
            "📂 Menu de Investimentos:\nEscolha uma opção:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def handle_balance(self, update: Update, context: CallbackContext) -> None:
        try:
            user_id = update.effective_user.id
            balance = self.db.get_balance(user_id)  

            if balance is None:
                await update.message.reply_text("⚠️ Não foi possível recuperar o saldo.")
                return

            await update.message.reply_text(
                f"💰 Seu saldo atual é: R$ {balance:.2f}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Atualizar", callback_data='sync_balance')],
                    [InlineKeyboardButton("📋 Ver Extrato", callback_data='statement')],
                    [InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')]
                ])
            )
        except Exception as e:
            logger.error(f"Erro ao obter saldo: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Ocorreu um erro ao obter o saldo. Tente novamente mais tarde.")
    
    async def handle_statement(self, update: Update, context: CallbackContext) -> None:
        """Exibe últimas transações do usuário"""
        try:
            user_id = update.effective_user.id
            transactions = self.db.get_last_transactions(user_id, limit=5)

            if not transactions:
                response = "📋 Nenhuma transação encontrada."
            else:
                response = "📋 Últimas transações:"
                for t in transactions:
                    response += f"• {t['date']}: {t['description']} - R$ {t['amount']:.2f} ({t['category']})"

            keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                await update.message.reply_text(response, reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.edit_message_text(response, reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Erro ao obter extrato: {str(e)}", exc_info=True)
            if update.message:
                await update.message.reply_text("❌ Ocorreu um erro ao obter seu extrato. Tente novamente mais tarde.")
            elif update.callback_query:
                await update.callback_query.edit_message_text("❌ Ocorreu um erro ao obter seu extrato.")
        try:
            user_id = update.effective_user.id
            transactions = self.db.get_last_transactions(user_id, limit=5)

            if not transactions:
                text = "📭 Nenhuma transação encontrada."
            else:
                text = "📋 Últimas transações:\n"
                for t in transactions:
                    text += f"\n• {t['date']}: {t['description']} - R$ {t['amount']:.2f} ({t.get('category', '-')})"

            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.reply_text(text)
            else:
                await update.message.reply_text(text)

        except Exception as e:
            logger.error(f"Erro ao obter extrato: {e}", exc_info=True)
            if update.callback_query:
                await update.callback_query.message.reply_text("❌ Ocorreu um erro ao obter seu extrato. Tente novamente mais tarde.")
            else:
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
                [InlineKeyboardButton("❌ Cancelar", callback_data='cancel_of')],
                [InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')]

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
                [InlineKeyboardButton("❌ Cancelar", callback_data='cancel_upload')],
                [InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')]
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
            transactions = self.analysis.process_file(file_path, bank_type, user.id)

            await update.message.reply_text(
                f"✅ Extrato processado com sucesso!\n\n"
                f"• Banco: {bank_type.value}\n"
                f"• Transações importadas: {len(transactions)}\n"
                f"• Saldo atualizado: R$ {self.db.get_balance(user.id):.2f}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Ver Extrato", callback_data='statement')],
                    [InlineKeyboardButton("🔙 Voltar", callback_data='back_to_menu')]
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


    async def handle_back_to_menu(self, update: Update, context: CallbackContext) -> None:
        """Retorna ao menu principal (mesmo do /start)"""
        try:
            if update.callback_query:
                await update.callback_query.answer()
                await self.start(update, context)
            else:
                await self.start(update, context)
        except Exception as e:
            logger.error(f"Erro ao voltar ao menu: {str(e)}", exc_info=True)
            await self.send_error_message(update, "Erro ao voltar ao menu principal.")

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