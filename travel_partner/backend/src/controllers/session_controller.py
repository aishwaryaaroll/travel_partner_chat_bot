"""Business logic behind the HTTP routes."""

from __future__ import annotations

from agents.travel_planner.agent import AgentError
from agents.travel_planner.questionnaire import first_question, missing_core, needs_destination_choice
from agents.travel_planner.validation import redact_sensitive

from ..config import Settings
from ..services.agent_service import AgentService, AgentTimeout
from ..services.pdf_service import render_itinerary_pdf
from ..services.session_store import Session, SessionLimitError, SessionStore
from ..utils.errors import ApiError, not_found
from ..validators.requests import ChatRequest, ConfirmRequest, ItineraryState, SessionState

GREETING = (
    "Hi! I'm your Travel Partner. Tell me a little about the trip you're dreaming of and I'll "
    "sketch out a day-by-day plan. You can answer the cards below or just type freely, "
    "and skip anything you're unsure about."
)
PRIVACY_NOTICE = (
    "I removed something that looked like sensitive information (such as a card, ID or passport "
    "number). I never need those to plan your trip."
)


class SessionController:
    def __init__(self, store: SessionStore, agent: AgentService | None, settings: Settings) -> None:
        self._store = store
        self._agent = agent
        self._settings = settings

    def _get(self, session_id: str) -> Session:
        session = self._store.get(session_id)
        if session is None:
            raise not_found()
        return session

    def _state(self, session: Session, reply: str | None = None, notice: str | None = None) -> SessionState:
        if session.confirmed_version and session.confirmed_version == session.latest_version:
            stage = "confirmed"
        elif session.versions:
            stage = "drafting"
        else:
            stage = "gathering"
        used = len(session.messages) // 2
        return SessionState(
            reply=reply,
            notice=notice,
            question=session.pending_question,
            preferences=session.preferences,
            stage=stage,
            itinerary=ItineraryState(
                itinerary=session.latest,
                version=session.latest_version,
                confirmed_version=session.confirmed_version,
            ),
            messages_remaining=max(0, self._settings.max_messages_per_session // 2 - used),
            open_core_questions=len(missing_core(session.preferences)),
            ready_to_generate=not missing_core(session.preferences),
            awaiting_destination_choice=needs_destination_choice(session.preferences),
        )

    def create(self) -> SessionState:
        try:
            session = self._store.create()
        except SessionLimitError:
            raise ApiError(503, "busy", "We're very busy right now. Please try again shortly.") from None
        session.pending_question = first_question()
        session.messages.append({"role": "assistant", "content": GREETING})
        state = self._state(session, reply=GREETING)
        state.session_id = session.id
        return state

    def get(self, session_id: str) -> SessionState:
        return self._state(self._get(session_id))

    async def chat(self, session_id: str, request: ChatRequest) -> SessionState:
        session = self._get(session_id)
        if self._agent is None:
            raise ApiError(
                503,
                "agent_not_configured",
                "The travel agent isn't configured yet. Add ANTHROPIC_API_KEY to personal-info/.env.",
            )
        if len(session.messages) // 2 >= self._settings.max_messages_per_session // 2:
            raise ApiError(
                429, "conversation_limit", "This conversation has reached its message limit. Please start a new trip."
            )
        if session.lock.locked():
            raise ApiError(409, "busy", "I'm still working on your last message.")

        message, redacted = redact_sensitive(request.message)
        async with session.lock:
            try:
                result = await self._agent.chat(session, message, request.skip_question, request.answering)
            except AgentTimeout:
                raise ApiError(
                    504, "agent_timeout", "That took too long. Please try again, maybe with a simpler request."
                ) from None
            except AgentError as exc:
                raise ApiError(502, "agent_error", str(exc)) from None
        return self._state(session, reply=result.reply, notice=PRIVACY_NOTICE if redacted else None)

    def confirm(self, session_id: str, request: ConfirmRequest) -> SessionState:
        session = self._get(session_id)
        if not session.versions:
            raise ApiError(409, "no_itinerary", "There's no itinerary to confirm yet.")
        if request.version != session.latest_version:
            raise ApiError(
                409, "stale_version", "The itinerary changed. Please review the latest version before confirming."
            )
        session.confirmed_version = request.version
        return self._state(session)

    def pdf(self, session_id: str) -> bytes:
        session = self._get(session_id)
        itinerary = session.confirmed
        if itinerary is None or session.confirmed_version is None:
            raise ApiError(409, "not_confirmed", "Please confirm your itinerary before downloading it.")
        return render_itinerary_pdf(itinerary, session.confirmed_version)

    def delete(self, session_id: str) -> None:
        self._store.delete(session_id)
