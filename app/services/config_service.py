from sqlalchemy.orm import Session

from app.models import Config
from app.schemas import NotionConfig, OpenRouterConfig, TelegramConfig


def get_config_value(db: Session, key: str) -> str | None:
    config_item = db.query(Config).filter(Config.key == key).first()
    return config_item.value if config_item else None


def set_config_value(db: Session, key: str, value: str | None):
    db_config = db.query(Config).filter(Config.key == key).first()
    if db_config:
        db_config.value = value
        return
    db_config = Config(key=key, value=value)
    db.add(db_config)


def get_config(db: Session):
    notion_config = NotionConfig()
    openrouter_config = OpenRouterConfig()
    telegram_config = TelegramConfig()

    for key in notion_config.model_dump().keys():
        value = get_config_value(db, key)
        setattr(notion_config, key, value)

    for key in openrouter_config.model_dump().keys():
        value = get_config_value(db, key)
        setattr(openrouter_config, key, value)

    for key in telegram_config.model_dump().keys():
        value = get_config_value(db, key)
        setattr(telegram_config, key, value)

    return {
        "notion": notion_config,
        "openrouter": openrouter_config,
        "telegram": telegram_config,
    }
