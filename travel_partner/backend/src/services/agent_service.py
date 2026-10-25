"""Wraps the travel agent with a timeout and maps its output onto a session."""

from __future__ import annotations

import asyncio
import logging

from agents.travel_planner.agent import AgentError, TravelAgent, TurnInput, TurnResult
from agents.travel_planner.questionnaire import mark_answered, mark_skipped, missing_core, needs_destination_choice

from .session_store import Session

log = logging.getLogger("travel_partner.agent_service")


class AgentTimeout(RuntimeError):
    pass


class AgentService:
    def __init__(self, agent: TravelAgent, timeout_seconds: float) -> None:
        self._agent = agent
        self._timeout = timeout_seconds

    async def chat(
        self,
        session: Session,
        message: str,
        skip_question: str | None,
        answering: str | None = None,
    ) -> TurnResult:
        if skip_question:
            session.preferences = mark_skipped(session.preferences, skip_question)
        if answering and answering != skip_question:
            session.preferences = mark_answered(session.preferences, answering)

        turn = TurnInput(
            message=message,
            preferences=session.preferences,
            history=list(session.messages),
            itinerary=session.latest,
            itinerary_version=session.latest_version,
            confirmed=session.confirmed_version is not None and session.confirmed_version == session.latest_version,
        )
        try:
            result = await asyncio.wait_for(self._agent.run_turn(turn), timeout=self._timeout)
        except TimeoutError:
            log.warning("agent turn timed out")
            raise AgentTimeout from None

        missing = missing_core(result.preferences)
        itinerary = result.itinerary
        if itinerary is not None and (missing or needs_destination_choice(result.preferences)):
            # Second line of defence behind the submit_itinerary tool check.
            log.warning("discarded itinerary submitted before the initial questions were settled")
            itinerary = None

        question = result.question
        if itinerary is None and missing and (question is None or question.key not in {q.key for q in missing}):
            # Keep the six initial question cards moving even if the model didn't ask one.
            question = missing[0]

        session.messages.append({"role": "user", "content": message})
        session.messages.append({"role": "assistant", "content": result.reply})
        session.preferences = result.preferences
        session.pending_question = question
        if itinerary is not None:
            session.versions.append(itinerary)
        return TurnResult(reply=result.reply, preferences=result.preferences, question=question, itinerary=itinerary)


__all__ = ["AgentError", "AgentService", "AgentTimeout"]
