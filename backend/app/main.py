from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    analytics,
    balances,
    bot_control,
    candidates,
    event_analyses,
    health,
    positions,
    rejections,
    status,
    trades,
    x_enrichments,
)
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(get_settings().log_level)
    get_settings().validate_mode_requirements()
    yield


app = FastAPI(title="Stonks API", lifespan=lifespan)
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_settings.frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analytics.router)
app.include_router(status.router)
app.include_router(balances.router)
app.include_router(positions.router)
app.include_router(trades.router)
app.include_router(event_analyses.router)
app.include_router(candidates.router)
app.include_router(rejections.router)
app.include_router(x_enrichments.router)
app.include_router(bot_control.router)


@app.get("/")
def root() -> dict:
    return {"service": "stonks", "docs": "/docs"}
