from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from openclaw_hatchling.daemon.config import HatchlingConfig

_security = HTTPBearer()


def create_app(
    *,
    config: HatchlingConfig,
    session_factory: async_sessionmaker[AsyncSession],
    data_dir: Path,
) -> FastAPI:
    app = FastAPI(title="OpenClaw Hatchling", docs_url=None, redoc_url=None)

    # Store shared state on the app instance
    app.state.config = config
    app.state.session_factory = session_factory
    app.state.data_dir = data_dir

    # Read the API token once at startup
    token_path = data_dir / "api_token"
    app.state.api_token = token_path.read_text().strip()

    # Register routers
    from openclaw_hatchling.api.attention import router as attention_router
    from openclaw_hatchling.api.birth import router as birth_router
    from openclaw_hatchling.api.care import router as care_router
    from openclaw_hatchling.api.export_import import router as export_import_router
    from openclaw_hatchling.api.rest import router as rest_router
    from openclaw_hatchling.api.status import router as status_router
    from openclaw_hatchling.api.talk import router as talk_router

    app.include_router(birth_router)
    app.include_router(status_router)
    app.include_router(care_router)
    app.include_router(talk_router)
    app.include_router(rest_router)
    app.include_router(attention_router)
    app.include_router(export_import_router)

    return app


async def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> str:
    """FastAPI dependency that validates the bearer token."""
    if credentials.credentials != request.app.state.api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return credentials.credentials


async def get_session(request: Request) -> Any:
    """FastAPI dependency that yields a database session."""
    async with request.app.state.session_factory() as session:
        yield session
