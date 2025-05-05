import logging
import os
import sys
import time
from datetime import datetime, timezone

import telegram
from telegram.constants import ParseMode
from telegram.error import TelegramError

# --- Path Setup ---
# Add project root to the Python path to allow importing 'app' modules
# Assumes this script is in app/telegram_bot/
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app.database import SessionLocal
    from app.services import config_service, flashcard_service
    from app.telegram_bot.handlers import format_flashcard # Reuse formatting logic
except ImportError as e:
    print(f"Error importing application modules: {e}", file=sys.stderr)
    print(f"Ensure the script is run from the project root or PYTHONPATH is set correctly.", file=sys.stderr)
    print(f"Project root determined as: {project_root}", file=sys.stderr)
    sys.exit(1)


# --- Logging Setup ---
# Configure logging to output to stdout for cron jobs or systemd logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
# Reduce verbosity from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_BATCH_SIZE = 5 # Number of flashcards to send per run
RATE_LIMIT_DELAY = 1 # Seconds to wait between messages if needed


def send_pending_flashcards():
    """
    Fetches pending flashcards from the database, sends them via Telegram,
    and updates their status. Intended to be run as a scheduled task.
    """
    start_time = time.time()
    logger.info("Starting scheduled task: send_pending_flashcards")
    db = SessionLocal()
    sent_count = 0
    failed_count = 0
    skipped_count = 0

    try:
        # --- Get Configuration ---
        token = config_service.get_config_value(db, "telegram_bot_token")
        chat_id_str = config_service.get_config_value(db, "telegram_chat_id")

        if not token:
            logger.error("Telegram Bot Token not found in configuration. Cannot send messages.")
            return # Critical config missing
        if not chat_id_str:
            logger.error("Telegram Chat ID not found in configuration. Cannot send messages.")
            return # Critical config missing

        try:
            chat_id = int(chat_id_str)
        except ValueError:
            logger.error(f"Invalid Telegram Chat ID configured: {chat_id_str}. Cannot send messages.")
            return # Critical config invalid

        logger.info(f"Configuration loaded. Target Chat ID: {chat_id}")

        # --- Get Pending Flashcards ---
        try:
            pending_cards = flashcard_service.get_pending_flashcards(db, limit=DEFAULT_BATCH_SIZE)
        except Exception as e:
            logger.error(f"Failed to query pending flashcards from database: {e}", exc_info=True)
            return # Cannot proceed without cards

        if not pending_cards:
            logger.info("No pending flashcards found to send.")
            return

        logger.info(f"Found {len(pending_cards)} pending flashcards to process (max {DEFAULT_BATCH_SIZE}).")

        # --- Initialize Bot ---
        try:
            bot = telegram.Bot(token=token)
            # Test connection/token validity early
            bot_info = bot.get_me()
            logger.info(f"Initialized Telegram Bot: {bot_info.username} (ID: {bot_info.id})")
        except TelegramError as e:
            logger.error(f"Failed to initialize Telegram Bot or invalid token: {e}")
            return # Cannot proceed without valid bot

        # --- Send Messages ---
        for card in pending_cards:
            logger.debug(f"Processing flashcard ID {card.id}")
            # Basic formatting, consider escaping special Markdown characters if using MarkdownV2
            message_text = f"*New Flashcard!*\n\n{format_flashcard(card)}"

            try:
                # Send the message
                bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode=ParseMode.MARKDOWN_V2 # Use MarkdownV2 for formatting
                    # Consider adding disable_web_page_preview=True if needed
                )
                logger.info(f"Successfully sent flashcard ID {card.id} to chat ID {chat_id}")
                sent_successfully = True

            except TelegramError as e:
                logger.error(f"Telegram API error sending flashcard ID {card.id}: {e}")
                # Decide on error handling: skip, retry, mark as failed?
                # For now, log as failed and continue to next card.
                failed_count += 1
                sent_successfully = False
                # Example: Mark as failed status
                # flashcard_service.update_flashcard_status(db, card.id, "failed")

            except Exception as e:
                logger.error(f"Unexpected error sending flashcard ID {card.id}: {e}", exc_info=True)
                failed_count += 1
                sent_successfully = False

            # --- Update Status if Sent Successfully ---
            if sent_successfully:
                try:
                    now_utc = datetime.now(timezone.utc)
                    success = flashcard_service.update_flashcard_status(
                        db, card.id, "sent", sent_at=now_utc
                    )
                    if success:
                        logger.info(f"Successfully updated status for flashcard ID {card.id} to 'sent'")
                        sent_count += 1
                    else:
                        # This case should be rare if the card existed initially
                        logger.error(f"Failed to update status for flashcard ID {card.id} after sending (card not found?).")
                        # Treat as failure for summary counts
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to update database status for flashcard ID {card.id} after sending: {e}", exc_info=True)
                    # Treat as failure for summary counts
                    failed_count += 1

            # Optional: Add a small delay between messages to avoid potential rate limits
            if len(pending_cards) > 1:
                 time.sleep(RATE_LIMIT_DELAY)


    except Exception as e:
        logger.critical(f"An unhandled error occurred during the send_pending_flashcards task: {e}", exc_info=True)
    finally:
        if db:
            db.close()
            logger.debug("Database session closed.")
        end_time = time.time()
        duration = end_time - start_time
        logger.info(
            f"Finished scheduled task: send_pending_flashcards in {duration:.2f} seconds. "
            f"Sent: {sent_count}, Failed: {failed_count}, Skipped: {skipped_count}"
        )


if __name__ == "__main__":
    send_pending_flashcards()
