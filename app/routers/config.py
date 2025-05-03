from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Config
from app.schemas import ConfigItem, ConfigUpdate
from app.database import get_db

router = APIRouter()

def get_config_value(db: Session, key: str) -> str | None:
    config_item = db.query(Config).filter(Config.key == key).first()
    return config_item.value if config_item else None

@router.get("/config", response_model=dict)
async def get_config(db: Session = Depends(get_db)):
    return {
        "notion_api_key": get_config_value(db, "notion_api_key"),
        "notion_database_id": get_config_value(db, "notion_database_id"),
        "openrouter_api_key": get_config_value(db, "openrouter_api_key"),
        "telegram_bot_token": get_config_value(db, "telegram_bot_token"),
        "telegram_chat_id": get_config_value(db, "telegram_chat_id")
    }

@router.post("/config")
async def update_config(config: ConfigUpdate, db: Session = Depends(get_db)):
    config_dict = config.dict()
    for key, value in config_dict.items():
        if value is not None:
            db_config = db.query(Config).filter(Config.key == key).first()
            if db_config:
                db_config.value = value
            else:
                db_config = Config(key=key, value=value)
                db.add(db_config)
    db.commit()
    return {"message": "Configuration updated successfully"}
