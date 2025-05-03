from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.config import get_config_value

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/config", response_class=HTMLResponse)
async def get_config_page(request: Request, db: Session = Depends(get_db)):
    config = {
        "notion_api_key": get_config_value(db, "notion_api_key"),
        "notion_database_id": get_config_value(db, "notion_database_id"),
        "openrouter_api_key": get_config_value(db, "openrouter_api_key"),
        "telegram_bot_token": get_config_value(db, "telegram_bot_token"),
        "telegram_chat_id": get_config_value(db, "telegram_chat_id")
    }
    return templates.TemplateResponse("config.html", {"request": request, "config": config})

@router.post("/config", response_class=HTMLResponse)
async def update_config_page(
    request: Request,
    notion_api_key: str = Form(None),
    notion_database_id: str = Form(None),
    openrouter_api_key: str = Form(None),
    telegram_bot_token: str = Form(None),
    telegram_chat_id: str = Form(None),
    db: Session = Depends(get_db)
):
    from app.models import Config
    
    config_updates = {
        "notion_api_key": notion_api_key,
        "notion_database_id": notion_database_id,
        "openrouter_api_key": openrouter_api_key,
        "telegram_bot_token": telegram_bot_token,
        "telegram_chat_id": telegram_chat_id
    }
    
    for key, value in config_updates.items():
        if value is not None and value.strip() != "":
            db_config = db.query(Config).filter(Config.key == key).first()
            if db_config:
                db_config.value = value
            else:
                db_config = Config(key=key, value=value)
                db.add(db_config)
    
    db.commit()
    
    config = {
        "notion_api_key": get_config_value(db, "notion_api_key"),
        "notion_database_id": get_config_value(db, "notion_database_id"),
        "openrouter_api_key": get_config_value(db, "openrouter_api_key"),
        "telegram_bot_token": get_config_value(db, "telegram_bot_token"),
        "telegram_chat_id": get_config_value(db, "telegram_chat_id")
    }
    
    return templates.TemplateResponse("config.html", {
        "request": request,
        "config": config,
        "message": "Configuration saved successfully!"
    })
