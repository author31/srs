from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import Config
from app.schemas import ConfigUpdate, NotionConfig, OpenRouterConfig, TelegramConfig
from app.database import get_db

router = APIRouter()


def get_config_value(db: Session, key: str) -> str | None:
    config_item = db.query(Config).filter(Config.key == key).first()
    return config_item.value if config_item else None


def set_config_value(db: Session, key: str, value: str | None):
    db_config = db.query(Config).filter(Config.key == key).first()
    if db_config:
        db_config.value = value
    else:
        db_config = Config(key=key, value=value)
        db.add(db_config)


@router.get("/config", response_model=dict)
async def get_config(db: Session = Depends(get_db)):
    notion_config = NotionConfig()
    openrouter_config = OpenRouterConfig()
    telegram_config = TelegramConfig()

    for key in notion_config.model_dump().keys():
        value = get_config_value(db, f"notion_{key}")
        setattr(notion_config, key, value)

    for key in openrouter_config.model_dump().keys():
        value = get_config_value(db, f"openrouter_{key}")
        setattr(openrouter_config, key, value)

    for key in telegram_config.model_dump().keys():
        value = get_config_value(db, f"telegram_{key}")
        setattr(telegram_config, key, value)

    return {
        "notion": notion_config,
        "openrouter": openrouter_config,
        "telegram": telegram_config,
    }


@router.post("/config")
async def update_config(config: ConfigUpdate, db: Session = Depends(get_db)):
    if config.notion:
        for key, value in config.notion.model_dump().items():
            set_config_value(db, f"notion_{key}", value)

    if config.openrouter:
        for key, value in config.openrouter.model_dump().items():
            set_config_value(db, f"openrouter_{key}", value)

    if config.telegram:
        for key, value in config.telegram.model_dump().items():
            set_config_value(db, f"telegram_{key}", value)

    db.commit()
    return {"message": "Configuration updated successfully"}
