from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routers import config, dashboard
from app.models import Base
from app.database import engine
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(dashboard.router)


@app.get("/")
async def root():
    # TODO: redirect /dashboard
    return {"message": "SRS Flashcard Generator & Telegram Bot"}
