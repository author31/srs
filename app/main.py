from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routers import config, dashboard

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(dashboard.router)


@app.get("/")
async def root():
    return {"message": "LLM Flashcard Generator & Telegram Bot"}
