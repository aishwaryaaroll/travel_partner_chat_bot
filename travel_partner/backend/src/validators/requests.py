"""Request and response contracts for the HTTP API."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from agents.travel_planner.schemas import Itinerary, Preferences, Question

SessionHeader = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{20,64}$")]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatRequest(Strict):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    skip_question: Annotated[str, StringConstraints(pattern=r"^[a-z_]{1,40}$")] | None = None
    answering: Annotated[str, StringConstraints(pattern=r"^[a-z_]{1,40}$")] | None = None


class ConfirmRequest(Strict):
    version: int = Field(ge=1, le=1000)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


Stage = Literal["gathering", "drafting", "confirmed"]


class ItineraryState(BaseModel):
    itinerary: Itinerary | None
    version: int | None
    confirmed_version: int | None


class SessionState(BaseModel):
    """Full snapshot returned after every interaction."""

    session_id: str | None = None
    reply: str | None = None
    notice: str | None = None
    question: Question | None
    preferences: Preferences
    stage: Stage
    itinerary: ItineraryState
    messages_remaining: int
    open_core_questions: int = 0
    ready_to_generate: bool = False
    awaiting_destination_choice: bool = False
