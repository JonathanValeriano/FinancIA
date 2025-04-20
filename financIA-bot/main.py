#!/usr/bin/env python3
import logging
from telegram import Update  # ✅ Correção: importação do Update
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
print("🔍 NEWS_API_KEY:", Config.NEWS_API_KEY)
from src.financIA.integrations.open_finance import OpenFinanceIntegration
from src.financIA.services.analysis_service import AnalysisService

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
        ('enviar_extrato', "Envia extrato bancário"),
        ('incluir_ativo', "Adiciona um ativo (ação, FII, etc.)"),
        ('meus_ativos', "Lista seus ativos cadastrados")
    ])

def setup_handlers(application: Application, handlers: BotHandlers) -> None:
    """Configura todos os handlers do bot"""
    # Handlers de comandos
    command_handlers = [
        CommandHandler("start", handlers.start),
        CommandHandler("saldo", handlers.handle_balance),
        CommandHandler("extrato", handlers.handle_statement),
        # CommandHandler("conectar_openfinance", handlers.handle_open_finance_connect),
        # CommandHandler("sincronizar", handlers.handle_open_finance_sync),
        CommandHandler("enviar_extrato", handlers.initiate_file_upload),
        CommandHandler("incluir_ativo", handlers.handle_add_asset),
        CommandHandler("meus_ativos", handlers.handle_asset_list)
    ]

    # Handlers de callback (botões inline)
    callback_handlers = [
        CallbackQueryHandler(handlers.handle_balance, pattern='^balance$'),
        CallbackQueryHandler(handlers.handle_statement, pattern='^statement$'),
        # CallbackQueryHandler(handlers.handle_open_finance_connect, pattern='^connect_of$'),
        CallbackQueryHandler(handlers.handle_cancel_of, pattern='^cancel_of$'),
        # CallbackQueryHandler(handlers.handle_open_finance_sync, pattern='^sync_of$'),
        CallbackQueryHandler(handlers.initiate_file_upload, pattern='^upload_file$'),
        CallbackQueryHandler(handlers.handle_cancel_upload, pattern='^cancel_upload$'),
        CallbackQueryHandler(handlers.handle_add_asset, pattern='^add_asset$'),
        CallbackQueryHandler(handlers.handle_cancel_add_asset, pattern='^cancel_add_asset$'),
        CallbackQueryHandler(handlers.handle_asset_list, pattern='^list_assets$'),
        CallbackQueryHandler(handlers.handle_back_to_menu, pattern='^back_to_menu$'),
        CallbackQueryHandler(handlers.handle_investimentos_menu, pattern='^investimentos_menu$'),
        CallbackQueryHandler(handlers.handle_controle_menu, pattern='^controle_menu$'),
        # CallbackQueryHandler(handlers.handle_acompanhar_ativos, pattern='^acompanhar_ativos$'),
        # CallbackQueryHandler(handlers.handle_track_investments, pattern='^track_investments$'),
        CallbackQueryHandler(handlers.handle_acompanhar_ativos, pattern='^track_investments$'),


    ]

    # Handlers de mensagens
    message_handlers = [
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message),
        MessageHandler(filters.Document.ALL, handlers.handle_file_upload)
    ]

    # Adiciona todos os handlers de uma vez
    application.add_handlers(command_handlers + callback_handlers + message_handlers)
    application.add_handler(CallbackQueryHandler(handlers.handle_delete_asset, pattern=r"^delete_asset:"))



def main() -> None:
    """Ponto principal de execução"""
    try:
        Config.ensure_dirs()

        # ✅ Verifica se o token está definido
        if not Config.BOT_TOKEN:
            raise ValueError("🚫 BOT_TOKEN não está definido nas configurações.")

        # Inicializa serviços
        db_manager = DatabaseManager()

        # Configura Open Finance se disponível
        of_client = None
        if Config.OPEN_FINANCE_CLIENT_ID and Config.OPEN_FINANCE_CLIENT_SECRET:
            of_client = OpenFinanceIntegration(
                Config.OPEN_FINANCE_CLIENT_ID,
                Config.OPEN_FINANCE_CLIENT_SECRET,
                Config.OPEN_FINANCE_REDIRECT_URI
            )

        analysis_service = AnalysisService(db_manager, of_client)
        bot_handlers = BotHandlers(db_manager, analysis_service)

        # Configura e inicia o bot
        application = Application.builder() \
            .token(Config.BOT_TOKEN) \
            .post_init(post_init) \
            .build()

        setup_handlers(application, bot_handlers)

        logger.info("🤖 Bot iniciado. Pressione Ctrl+C para sair.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except KeyboardInterrupt:
        logger.info("⚠️ Bot finalizado pelo usuário (Ctrl+C)")
    except Exception as e:
        logger.exception(f"💥 Falha crítica na inicialização: {str(e)}")
        raise

if __name__ == "__main__":
    main()
