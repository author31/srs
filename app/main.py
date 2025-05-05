from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import LOCAL_DIR
from app.database import engine
from app.models import Base
from app.routers import config, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(LOCAL_DIR).mkdir(exist_ok=True)

    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(dashboard.router)


from fastapi.responses import RedirectResponse


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")
