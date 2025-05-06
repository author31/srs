from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import config_service, dashboard_service, knowledge_service

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


@router.get("/api/fetch", response_class=JSONResponse)
async def fetch_knowledge(
    db: Session = Depends(get_db),
):
    """
    Fetch knowledge from configured sources.
    If source is specified, only fetch from that source.
    """
    results = await knowledge_service.fetch_from_all_sources(db)
    return results
