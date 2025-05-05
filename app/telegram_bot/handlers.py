import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db # Use get_db if integrating with FastAPI context later
from app.services import flashcard_service, config_service

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def get_db_session() -> Session:
    """Creates a new database session. Replace with get_db if needed."""
    # In a standalone script or simple bot polling, creating a session per request is okay.
    # If integrating tightly with FastAPI, dependency injection (Depends(get_db)) is better.
    return SessionLocal()

def format_flashcard(flashcard) -> str:
    """Formats a flashcard object into a string for Telegram."""
    # Basic formatting, can be enhanced (e.g., Markdown)
    q = flashcard.question.strip()
    a = flashcard.answer.strip()
    source_info = f"{flashcard.knowledge_source_type} ({flashcard.knowledge_source_id})" if flashcard.knowledge_source_id else flashcard.knowledge_source_type
    return f"Q: {q}\nA: {a}\nSource: {source_info}"

async def check_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the message comes from the configured chat ID."""
    db = get_db_session()
    try:
        configured_chat_id_str = config_service.get_config_value(db, "telegram_chat_id")
        if not configured_chat_id_str:
            logger.warning("Telegram Chat ID not configured in database.")
            # Avoid replying in chats that are not the configured one
            # await update.message.reply_text("Bot not configured. Please set the Telegram Chat ID via the dashboard.")
            return False

        try:
            configured_chat_id = int(configured_chat_id_str)
        except ValueError:
            logger.error(f"Invalid Telegram Chat ID configured: {configured_chat_id_str}")
            return False

        if update.effective_chat.id != configured_chat_id:
            logger.warning(f"Ignoring message from unauthorized chat ID: {update.effective_chat.id}. Expected: {configured_chat_id}")
            return False
        logger.debug(f"Message received from authorized chat ID: {update.effective_chat.id}")
        return True
    except Exception as e:
        logger.error(f"Error checking chat ID: {e}", exc_info=True)
        return False # Fail safe
    finally:
        db.close()


# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    logger.info(f"Received /start command from chat ID: {update.effective_chat.id}")
    if not await check_chat_id(update, context):
        return
    await update.message.reply_text(
        "Hello! I'm the Flashcard Bot.\n\n"
        "I will send you new flashcards periodically.\n\n"
        "Available commands:\n"
        "/summary <today|this_month|last_three_months> - Review recently sent flashcards.\n"
        "/random [N] - Get N random flashcards (default 3, max 20)."
    )


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /summary command."""
    logger.info(f"Received /summary command from chat ID: {update.effective_chat.id} with args: {context.args}")
    if not await check_chat_id(update, context):
        return

    if not context.args:
        await update.message.reply_text("Usage: /summary <period>\nPeriods: today, this_month, last_three_months")
        return

    period = context.args[0].lower()
    valid_periods = ["today", "this_month", "last_three_months"]
    if period not in valid_periods:
        await update.message.reply_text(f"Invalid period '{period}'. Use one of: {', '.join(valid_periods)}")
        return

    db = get_db_session()
    try:
        flashcards = flashcard_service.get_sent_flashcards_by_period(db, period)
        if not flashcards:
            await update.message.reply_text(f"No flashcards found for the period: {period}.")
            return

        response_header = f"Flashcards sent for period '{period}' ({len(flashcards)} total):\n{'-'*20}\n"
        response_message = ""
        MAX_MSG_LEN = 4096 # Telegram message length limit

        await update.message.reply_text(response_header) # Send header first

        for card in flashcards:
            card_text = format_flashcard(card) + "\n\n"
            if len(response_message) + len(card_text) > MAX_MSG_LEN - 50: # Leave buffer
                await update.message.reply_text(response_message)
                response_message = card_text # Start new message
            else:
                response_message += card_text

        if response_message: # Send the last batch
             await update.message.reply_text(response_message.strip())

    except Exception as e:
        logger.error(f"Error processing /summary command for period '{period}': {e}", exc_info=True)
        await update.message.reply_text("An error occurred while fetching the summary. Please check the logs.")
    finally:
        db.close()


async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /random command."""
    logger.info(f"Received /random command from chat ID: {update.effective_chat.id} with args: {context.args}")
    if not await check_chat_id(update, context):
        return

    count = 3  # Default value
    MAX_RANDOM_COUNT = 20
    if context.args:
        try:
            count = int(context.args[0])
            if count <= 0 or count > MAX_RANDOM_COUNT:
                await update.message.reply_text(f"Please provide a number between 1 and {MAX_RANDOM_COUNT}.")
                return
        except (ValueError, IndexError):
            await update.message.reply_text("Invalid number. Usage: /random [N] (e.g., /random 5)")
            return

    db = get_db_session()
    try:
        flashcards = flashcard_service.get_random_flashcards(db, count)
        if not flashcards:
            await update.message.reply_text("No flashcards found in the database yet.")
            return

        response_header = f"Here are {len(flashcards)} random flashcard(s):\n{'-'*20}\n"
        response_message = ""
        MAX_MSG_LEN = 4096

        await update.message.reply_text(response_header) # Send header first

        for card in flashcards:
            card_text = format_flashcard(card) + "\n\n"
            if len(response_message) + len(card_text) > MAX_MSG_LEN - 50: # Leave buffer
                await update.message.reply_text(response_message)
                response_message = card_text # Start new message
            else:
                response_message += card_text

        if response_message: # Send the last batch
             await update.message.reply_text(response_message.strip())

    except Exception as e:
        logger.error(f"Error processing /random command for count {count}: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while fetching random flashcards. Please check the logs.")
    finally:
        db.close()

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unknown commands."""
    logger.info(f"Received unknown command from chat ID: {update.effective_chat.id}")
    if not await check_chat_id(update, context):
        return
    # Check if it's a message or command; only reply to commands we didn't understand
    if update.message and update.message.text and update.message.text.startswith('/'):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, I didn't understand that command. Try /start to see available commands."
        )

