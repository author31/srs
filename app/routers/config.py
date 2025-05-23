from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ConfigUpdate, NotionConfig, OpenRouterConfig, TelegramConfig
from app.services import config_service

router = APIRouter()


@router.get("/config", response_model=dict)
async def get_config(db: Session = Depends(get_db)):
    notion_config = NotionConfig()
    openrouter_config = OpenRouterConfig()
    telegram_config = TelegramConfig()

    for key in notion_config.model_dump().keys():
        value = config_service.get_config_value(db, f"notion_{key}")
        setattr(notion_config, key, value)

    for key in openrouter_config.model_dump().keys():
        value = config_service.get_config_value(db, f"openrouter_{key}")
        setattr(openrouter_config, key, value)

    for key in telegram_config.model_dump().keys():
        value = config_service.get_config_value(db, f"telegram_{key}")
        setattr(telegram_config, key, value)

    return {
        "notion": notion_config,
        "openrouter": openrouter_config,
        "telegram": telegram_config,
    }


@router.post("/config")
async def update_config(
    notion_api_key: str = Form(None),
    notion_database_id: str = Form(None),
    openrouter_api_key: str = Form(None),
    telegram_bot_token: str = Form(None),
    telegram_chat_id: str = Form(None),
    db: Session = Depends(get_db),
):
    notion_config = NotionConfig(
        notion_api_key=notion_api_key, notion_database_id=notion_database_id
    )
    openrouter_config = OpenRouterConfig(openrouter_api_key=openrouter_api_key)
    telegram_config = TelegramConfig(
        telegram_bot_token=telegram_bot_token, telegram_chat_id=telegram_chat_id
    )

    config_update = ConfigUpdate(
        notion=notion_config, openrouter=openrouter_config, telegram=telegram_config
    )

    if config_update.notion:
        for key, value in config_update.notion.model_dump().items():
            config_service.set_config_value(db, key, value)

    if config_update.openrouter:
        for key, value in config_update.openrouter.model_dump().items():
            config_service.set_config_value(db, key, value)

    if config_update.telegram:
        for key, value in config_update.telegram.model_dump().items():
            config_service.set_config_value(db, key, value)

    db.commit()

    # Redirect back to the dashboard with a success message
    query_params = {"message": "Configuration saved successfully!"}
    return RedirectResponse(f"/dashboard?{urlencode(query_params)}", status_code=303)
