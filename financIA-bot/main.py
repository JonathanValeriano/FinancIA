#!/usr/bin/env python3
import logging
from telegram.ext import Application, CommandHandler
from financIA.config import Config
from financIA.core.database import DatabaseManager
from financIA.bot.handlers import BotHandlers

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
    ])

def setup_handlers(application: Application, handlers: BotHandlers) -> None:
    """Configura todos os handlers do bot"""
    # Comandos básicos
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("saldo", handlers.handle_balance))
    application.add_handler(CommandHandler("extrato", handlers.handle_statement))

    # Handler para mensagens não-comando
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
        bot_handlers = BotHandlers(db_manager)
        
        # Cria e configura a aplicação
        application = Application.builder() \
            .token(Config.BOT_TOKEN) \
            .post_init(post_init) \
            .build()
        
        setup_handlers(application, bot_handlers)
        
        logger.info("Bot iniciado. Press Ctrl+C to exit.")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Falha na inicialização: {e}")
        raise

if __name__ == "__main__":
    main()