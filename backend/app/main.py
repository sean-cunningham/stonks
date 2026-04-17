from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api import (
    analytics,
    balances,
    bot_control,
    candidates,
    decisions,
    event_analyses,
    health,
    positions,
    rejections,
    status,
    trades,
    x_enrichments,
)
from app.api.strategies import unified as strategies_unified
from app.core.config import get_settings
from app.core.logging import configure_logging

log = logging.getLogger(__name__)


def _cors_headers_for_request(request: Request, settings) -> dict[str, str]:
    origin = request.headers.get("origin") or ""
    allowed = {settings.frontend_origin, "http://127.0.0.1:5173", "http://localhost:5173"}
    if origin not in allowed:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(get_settings().log_level)
    get_settings().validate_mode_requirements()
    yield


app = FastAPI(title="Stonks API", lifespan=lifespan)
_settings = get_settings()


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    # Unhandled DB errors bypass CORSMiddleware's response wrapper → browser shows TypeError: Failed to fetch.
    log.exception("database operational error")
    headers = _cors_headers_for_request(request, _settings)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database error (often missing migrations). Run: alembic upgrade head",
        },
        headers=headers,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[_settings.frontend_origin, "http://127.0.0.1:5173", "http://localhost:5173"],
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
app.include_router(decisions.router)
app.include_router(event_analyses.router)
app.include_router(candidates.router)
app.include_router(rejections.router)
app.include_router(x_enrichments.router)
app.include_router(bot_control.router)
app.include_router(strategies_unified.router)


@app.get("/")
def root() -> dict:
    return {"service": "stonks", "docs": "/docs"}
