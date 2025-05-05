import logging
from datetime import UTC, datetime

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.models import Flashcard

logger = logging.getLogger(__name__)


def get_pending_flashcards(db: Session, limit: int = 10) -> list[Flashcard]:
    """Retrieves flashcards with 'pending' status."""
    logger.info(f"Querying for up to {limit} pending flashcards.")
    try:
        cards = db.query(Flashcard).filter(Flashcard.status == "pending").limit(limit).all()
        logger.info(f"Found {len(cards)} pending flashcards.")
        return cards
    except Exception as e:
        logger.error(f"Error querying pending flashcards: {e}", exc_info=True)
        raise # Re-raise the exception after logging


def update_flashcard_status(
    db: Session, flashcard_id: int, new_status: str, sent_at: datetime | None = None
) -> bool:
    """Updates the status and optionally sent_at timestamp of a flashcard."""
    logger.info(f"Updating flashcard ID {flashcard_id} to status '{new_status}'.")
    try:
        stmt = (
            update(Flashcard)
            .where(Flashcard.id == flashcard_id)
            .values(status=new_status, sent_at=sent_at)
        )
        result = db.execute(stmt)
        db.commit()
        if result.rowcount > 0:
            logger.info(f"Successfully updated flashcard ID {flashcard_id}.")
            return True
        else:
            logger.warning(f"Flashcard ID {flashcard_id} not found for status update.")
            return False
    except Exception as e:
        logger.error(f"Error updating flashcard {flashcard_id} status: {e}", exc_info=True)
        db.rollback()
        return False


def get_sent_flashcards_by_period(
    db: Session, period: str
) -> list[Flashcard]:
    """
    Retrieves flashcards marked as 'sent' within a specific period.

    Args:
        db: The database session.
        period: 'today', 'this_month', or 'last_three_months'.

    Returns:
        A list of Flashcard objects. Returns empty list if period is invalid or no cards found.
    """
    logger.info(f"Querying sent flashcards for period: {period}")
    now = datetime.now(UTC)
    start_date = None

    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "this_month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "last_three_months":
        # Calculate the first day of the month three months ago
        month = now.month - 3
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        # Handle potential day issues (e.g., requesting 31st from a month with 30 days)
        # Safest is to just go to the first day of that month
        start_date = now.replace(
            year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    else:
        logger.warning(f"Invalid period specified for summary: {period}")
        return []  # Return empty list for invalid period

    logger.info(f"Calculated start date for period '{period}': {start_date}")
    try:
        cards = (
            db.query(Flashcard)
            .filter(Flashcard.status == "sent", Flashcard.sent_at >= start_date)
            .order_by(Flashcard.sent_at.asc())
            .all()
        )
        logger.info(f"Found {len(cards)} sent flashcards for period '{period}'.")
        return cards
    except Exception as e:
        logger.error(f"Error querying sent flashcards for period '{period}': {e}", exc_info=True)
        raise


def get_random_flashcards(db: Session, count: int = 3) -> list[Flashcard]:
    """Retrieves a specified number of random flashcards (any status)."""
    logger.info(f"Querying for {count} random flashcards.")
    try:
        # Using SQLAlchemy's func.random() which should translate appropriately for supported backends (SQLite, PostgreSQL)
        cards = db.query(Flashcard).order_by(func.random()).limit(count).all()
        logger.info(f"Found {len(cards)} random flashcards.")
        return cards
    except Exception as e:
        logger.error(f"Error querying random flashcards: {e}", exc_info=True)
        raise

