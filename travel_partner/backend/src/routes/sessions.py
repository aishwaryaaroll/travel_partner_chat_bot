"""HTTP routes. The session token travels in the ``X-Session-Id`` header."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response

from ..config import get_settings
from ..controllers.session_controller import SessionController
from ..middleware.rate_limit import limiter
from ..validators.requests import ChatRequest, ConfirmRequest, SessionHeader, SessionState

router = APIRouter(prefix="/api")

SessionId = Annotated[SessionHeader, Header(alias="X-Session-Id")]


def controller(request: Request) -> SessionController:
    return request.app.state.controller


Controller = Annotated[SessionController, Depends(controller)]


@router.get("/health")
async def health(request: Request) -> dict:
    return {"status": "ok", "agent_configured": request.app.state.controller_agent_ready}


@router.post("/sessions", status_code=201)
@limiter.limit("10/minute")
async def create_session(request: Request, ctl: Controller) -> SessionState:
    return ctl.create()


@router.get("/session")
async def get_session(request: Request, ctl: Controller, session_id: SessionId) -> SessionState:
    return ctl.get(session_id)


@router.delete("/session", status_code=204)
async def delete_session(request: Request, ctl: Controller, session_id: SessionId) -> Response:
    ctl.delete(session_id)
    return Response(status_code=204)


@router.post("/chat")
@limiter.limit(get_settings().rate_limit_chat)
async def chat(request: Request, body: ChatRequest, ctl: Controller, session_id: SessionId) -> SessionState:
    return await ctl.chat(session_id, body)


@router.post("/itinerary/confirm")
async def confirm(request: Request, body: ConfirmRequest, ctl: Controller, session_id: SessionId) -> SessionState:
    return ctl.confirm(session_id, body)


@router.get("/itinerary/pdf")
@limiter.limit("10/minute")
async def download_pdf(request: Request, ctl: Controller, session_id: SessionId) -> Response:
    pdf = ctl.pdf(session_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="travel-itinerary.pdf"'},
    )
