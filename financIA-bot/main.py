#!/usr/bin/env python3
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from src.financIA.core.database import DatabaseManager
from src.financIA.bot.handlers import BotHandlers
from src.financIA.config import Config
from src.integrations.open_finance import OpenFinanceIntegration
from src.services.analysis_service import AnalysisService

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """Rotina de inicialização com comandos atualizados"""
    await application.bot.set_my_commands([
        ('start', "Inicia o bot"),
        ('saldo', "Mostra seu saldo atual"),
        ('extrato', "Mostra últimas transações"),
        ('conectar_openfinance', "Conecta ao Open Finance"),
        ('sincronizar', "Sincroniza dados com Open Finance"),
        ('enviar_extrato', "Envia extrato bancário")
    ])

def setup_handlers(application: Application, handlers: BotHandlers) -> None:
    """Configura todos os handlers do bot"""
    # Comandos básicos
    command_handlers = [
        CommandHandler("start", handlers.start),
        CommandHandler("saldo", handlers.handle_balance),
        CommandHandler("extrato", handlers.handle_statement),
        CommandHandler("conectar_openfinance", handlers.handle_open_finance_connect),
        CommandHandler("sincronizar", handlers.handle_open_finance_sync),
        CommandHandler("enviar_extrato", handlers.initiate_file_upload)
    ]
    
    # Handlers para botões inline
    callback_handlers = [
        CallbackQueryHandler(handlers.handle_balance, pattern='^balance$'),
        CallbackQueryHandler(handlers.handle_statement, pattern='^statement$'),
        CallbackQueryHandler(handlers.handle_open_finance_connect, pattern='^connect_of$'),
        CallbackQueryHandler(handlers.handle_cancel_of, pattern='^cancel_of$'),
        CallbackQueryHandler(handlers.handle_open_finance_sync, pattern='^sync_of$'),
        CallbackQueryHandler(handlers.initiate_file_upload, pattern='^upload_file$'),
        CallbackQueryHandler(handlers.handle_cancel_upload, pattern='^cancel_upload$')
    ]
    
    # Handlers para mensagens
    message_handlers = [
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message),
        MessageHandler(filters.Document.ALL, handlers.handle_file_upload)
    ]
    
    # Adiciona todos os handlers
    application.add_handlers(command_handlers + callback_handlers + message_handlers)

def main() -> None:
    """Ponto principal de execução"""
    try:
        Config.ensure_dirs()
        
        # Inicializa componentes
        db_manager = DatabaseManager()
        
        # Configura Open Finance
        of_client = None
        if Config.OPEN_FINANCE_CLIENT_ID and Config.OPEN_FINANCE_CLIENT_SECRET:
            of_client = OpenFinanceIntegration(
                Config.OPEN_FINANCE_CLIENT_ID,
                Config.OPEN_FINANCE_CLIENT_SECRET,
                Config.OPEN_FINANCE_REDIRECT_URI
            )
        
        analysis_service = AnalysisService(db_manager, of_client)
        bot_handlers = BotHandlers(db_manager, analysis_service)
        
        # Cria e configura a aplicação
        application = Application.builder() \
            .token(Config.BOT_TOKEN) \
            .post_init(post_init) \
            .build()
        
        setup_handlers(application, bot_handlers)
        
        logger.info("Bot iniciado. Pressione Ctrl+C para sair.")
        application.run_polling()
        
    except Exception as e:
        logger.exception("Falha crítica na inicialização")
        raise

if __name__ == "__main__":
    main()