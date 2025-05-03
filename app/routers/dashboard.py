from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.config import get_config
from app.schemas import ConfigUpdate, NotionConfig, OpenRouterConfig, TelegramConfig

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/config", response_class=HTMLResponse)
async def get_config_page(request: Request, db: Session = Depends(get_db)):
    config = await get_config(db)
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
    from app.routers.config import update_config
    
    notion_config = NotionConfig(
        notion_api_key=notion_api_key,
        notion_database_id=notion_database_id
    )
    openrouter_config = OpenRouterConfig(
        openrouter_api_key=openrouter_api_key
    )
    telegram_config = TelegramConfig(
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id
    )
    
    config_update = ConfigUpdate(
        notion=notion_config,
        openrouter=openrouter_config,
        telegram=telegram_config
    )
    
    message = await update_config(config_update, db)
    
    config = await get_config(db)
    
    return templates.TemplateResponse("config.html", {
        "request": request,
        "config": config,
        "message": "Configuration saved successfully!"
    })
