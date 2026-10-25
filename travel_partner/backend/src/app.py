"""FastAPI application factory.

Run with:  uvicorn src.app:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from agents.travel_planner.agent import ClaudeTravelAgent, TravelAgent

from .config import Settings, get_settings
from .controllers.session_controller import SessionController
from .middleware.errors import register_error_handlers
from .middleware.rate_limit import limiter
from .middleware.security import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from .routes.sessions import router
from .services.agent_service import AgentService
from .services.session_store import SessionStore

# Log levels and event names only. Request bodies and conversation text are never logged.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None, agent: TravelAgent | None = None) -> FastAPI:
    settings = settings or get_settings()
    if agent is None and settings.agent_configured:
        agent = ClaudeTravelAgent(
            api_key=settings.anthropic_api_key.get_secret_value(),
            model=settings.model,
            max_turns=settings.agent_max_turns,
            max_budget_usd=settings.agent_max_budget_usd,
            timeout_seconds=settings.agent_timeout_seconds,
        )

    app = FastAPI(title="Travel Partner API", docs_url=None, redoc_url=None, openapi_url=None)
    store = SessionStore(ttl_seconds=settings.session_ttl_minutes * 60, max_sessions=settings.max_sessions)
    service = AgentService(agent, settings.agent_timeout_seconds) if agent else None
    app.state.controller = SessionController(store, service, settings)
    app.state.controller_agent_ready = service is not None
    app.state.limiter = limiter

    register_error_handlers(app)
    app.include_router(router)

    # Order: the last added runs first, so the body limit is applied before anything else.
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Session-Id"],
        expose_headers=["Content-Disposition"],
        max_age=600,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    return app


app = create_app()
