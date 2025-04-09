from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from src.financIA.core.database import DatabaseManager
from src.services.analysis_service import AnalysisService

class BotHandlers:
    def __init__(self, db: DatabaseManager, analysis: AnalysisService):
        self.db = db
        self.analysis = analysis
    
    async def start(self, update: Update, context: CallbackContext):
        """Menu principal agora com Open Finance"""
        user = update.effective_user
        keyboard = [
            [InlineKeyboardButton("📊 Saldo", callback_data='balance')],
            [InlineKeyboardButton("📋 Extrato", callback_data='statement')],
            [InlineKeyboardButton("🔗 Conectar Open Finance", callback_data='connect_of')]
        ]
        
        await update.message.reply_text(
            f"👋 Olá {user.first_name}! Eu sou seu assistente financeiro.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_balance(self, update: Update, context: CallbackContext):
        """Handler para o comando /saldo"""
        await update.message.reply_text("📊 Buscando seu saldo...")
    
    async def handle_statement(self, update: Update, context: CallbackContext):
        """Handler para o comando /extrato"""
        await update.message.reply_text("📋 Buscando suas transações...")
    
    async def handle_message(self, update: Update, context: CallbackContext):
        """Handler para mensagens não-comando"""
        await update.message.reply_text("Por favor use um comando ou toque nos botões abaixo:")
        await self.start(update, context)
    
    # --- Novos handlers para Open Finance ---
    
    async def handle_open_finance_connect(self, update: Update, context: CallbackContext):
        """Inicia o fluxo de conexão com Open Finance"""
        query = update.callback_query
        await query.answer()
        
        # 1. Explicação para o usuário
        await query.edit_message_text(
            "🔗 Para conectar seu banco via Open Finance:\n\n"
            "1. Acesse seu internet banking\n"
            "2. Procure por 'Open Finance' ou 'Compartilhamento de dados'\n"
            "3. Autorize o compartilhamento com 'FinancIA Bot'\n"
            "4. Envie-nos o código de autorização que você receber",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancelar", callback_data='cancel_of')]
            ])
        )
        
        # Guarda estado para próxima interação
        context.user_data['awaiting_of_token'] = True
    
    async def handle_open_finance_token(self, update: Update, context: CallbackContext):
        """Processa o token de autorização recebido"""
        if context.user_data.get('awaiting_of_token'):
            token = update.message.text
            
            try:
                # Aqui você implementaria a troca do token por access_token
                # Exemplo simplificado:
                account_id = self._exchange_token(token)
                
                # Salva no banco de dados
                self.db.save_open_finance_connection(
                    user_id=update.effective_user.id,
                    account_id=account_id,
                    token=token  # Na prática, armazene o access_token seguro
                )
                
                await update.message.reply_text(
                    "✅ Banco conectado com sucesso via Open Finance!\n"
                    f"Conta: {account_id}\n\n"
                    "Agora você pode:\n"
                    "- Visualizar saldo atualizado\n"
                    "- Receber análises automáticas"
                )
                
            except Exception as e:
                await update.message.reply_text(f"❌ Falha na conexão: {str(e)}")
            
            finally:
                context.user_data['awaiting_of_token'] = False
    
    async def handle_open_finance_sync(self, update: Update, context: CallbackContext):
        """Sincroniza dados via Open Finance"""
        user_id = update.effective_user.id
        account_info = self.db.get_of_connection(user_id)
        
        if not account_info:
            await update.message.reply_text("⚠️ Nenhum banco conectado. Use /conectar_openfinance")
            return
        
        try:
            count = self.analysis.process_source(
                source_type='open_finance',
                account_id=account_info['account_id'],
                start_date='2023-01-01',  # Ou data da última sincronização
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            await update.message.reply_text(
                f"🔄 Dados sincronizados com sucesso!\n"
                f"• {count} novas transações\n"
                f"• Saldo atual: R$ {self.db.get_balance(user_id):.2f}"
            )
        
        except Exception as e:
            await update.message.reply_text(f"❌ Falha na sincronização: {str(e)}")

    # --- Helper Methods ---
    
    def _exchange_token(self, auth_code: str) -> str:
        """Implemente a lógica real de troca de tokens aqui"""
        # Isso varia por banco, exemplo genérico:
        response = requests.post(
            "https://banco.api/openfinance/token",
            data={'grant_type': 'authorization_code', 'code': auth_code}
        )
        return response.json()['account_id']