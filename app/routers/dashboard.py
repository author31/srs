from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import dashboard_service, config_service

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request, db: Session = Depends(get_db)):
    config = config_service.get_config(db)
    flashcards = dashboard_service.get_flashcards(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "config": config, "flashcards": flashcards},
    )
