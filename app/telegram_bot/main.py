import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.database import SessionLocal
from app.services import config_service
from app.telegram_bot.handlers import (
    random_command,
    start_command,
    summary_command,
    unknown_command,
)

# Configure logging more robustly
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
# Reduce verbosity from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

    # Optionally, send a message to the chat where the error occurred or to a developer chat
    # Be cautious about sending detailed errors to users.
    # Consider sending a generic error message and logging the details.
    # traceback_str = "".join(traceback.format_exception(None, context.error, context.error.__traceback__))
    # logger.error(f"Traceback:\n{traceback_str}")

    # Example: Send generic error message if the update has a chat context
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, an internal error occurred while processing your request."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to chat {update.effective_chat.id}: {e}")


def run_bot():
    """Configures and runs the Telegram bot using polling."""
    logger.info("Attempting to start Telegram bot...")

    db = SessionLocal()
    try:
        token = config_service.get_config_value(db, "telegram_bot_token")
        # We don't strictly need the chat_id here, as handlers check it, but good to verify it exists.
        chat_id_str = config_service.get_config_value(db, "telegram_chat_id")
    finally:
        db.close()

    if not token:
        logger.critical("CRITICAL: Telegram Bot Token not found in configuration. Bot cannot start.")
        return # Exit if no token
    if not chat_id_str:
        logger.critical("CRITICAL: Telegram Chat ID not found in configuration. Bot will run but only respond if configured later.")
        return # Exit if no token

    try:
        application = Application.builder().token(token).build()

        # Register command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("summary", summary_command))
        application.add_handler(CommandHandler("random", random_command))

        # Handler for unknown commands - filters.COMMAND ensures it only catches commands
        application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

        # Start the Bot using polling
        logger.info("Starting bot polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES) # Listen for all update types

    except Exception as e:
        logger.critical(f"CRITICAL: Failed to initialize or run the Telegram bot: {e}", exc_info=True)


if __name__ == "__main__":
    run_bot()

