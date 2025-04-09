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

# Configuração básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """Rotina de inicialização"""
    await application.bot.set_my_commands([
        ('start', "Inicia o bot"),
        ('saldo', "Mostra seu saldo atual"),
        ('extrato', "Mostra últimas transações"),
        ('conectar_openfinance', "Conecta ao Open Finance")
    ])

def setup_handlers(application: Application, handlers: BotHandlers) -> None:
    """Configura todos os handlers do bot"""
    # Comandos básicos
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("saldo", handlers.handle_balance))
    application.add_handler(CommandHandler("extrato", handlers.handle_statement))
    application.add_handler(CommandHandler("conectar_openfinance", handlers.handle_open_finance_connect))

    # Handlers para botões inline
    application.add_handler(CallbackQueryHandler(handlers.handle_open_finance_connect, pattern='^connect_of$'))
    application.add_handler(CallbackQueryHandler(handlers.handle_cancel_of, pattern='^cancel_of$'))

    # Handler para mensagens não-comando (incluindo tokens Open Finance)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handlers.handle_message
    ))

def main() -> None:
    """Ponto principal de execução"""
    try:
        # Garante que diretórios existam
        Config.ensure_dirs()
        
        # Inicializa componentes
        db_manager = DatabaseManager()
        
        # Configura Open Finance se disponível
        of_client = None
        if Config.OPEN_FINANCE_CLIENT_ID and Config.OPEN_FINANCE_CLIENT_SECRET:
            of_client = OpenFinanceIntegration(
                Config.OPEN_FINANCE_CLIENT_ID,
                Config.OPEN_FINANCE_CLIENT_SECRET
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
        logger.error(f"Falha na inicialização: {e}")
        raise

if __name__ == "__main__":
    main()