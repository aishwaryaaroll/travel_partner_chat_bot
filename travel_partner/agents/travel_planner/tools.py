"""In-process MCP tools the model uses to report structured results.

The tools only record data on a per-turn ``TurnState``. They never touch the
file system, the network, or the environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool
from pydantic import ValidationError

from .questionnaire import (
    APP_CONTROLLED_FIELDS,
    known_question,
    merge_preferences,
    missing_core,
    needs_destination_choice,
)
from .schemas import Itinerary, Preferences, Question
from .validation import ItineraryValidationError, redact_sensitive, validate_itinerary

SERVER_NAME = "travel"
TOOL_NAMES = ["update_preferences", "ask_question", "submit_itinerary"]
ALLOWED_MCP_TOOLS = [f"mcp__{SERVER_NAME}__{name}" for name in TOOL_NAMES]

# Preferences the model may set. "skipped" and "answered" are controlled only by the app.
_PREFERENCE_SCHEMA = Preferences.model_json_schema()
for _field in APP_CONTROLLED_FIELDS:
    _PREFERENCE_SCHEMA["properties"].pop(_field, None)
_PREFERENCE_SCHEMA["additionalProperties"] = False

_QUESTION_SCHEMA = Question.model_json_schema()
_ITINERARY_SCHEMA = Itinerary.model_json_schema()


@dataclass
class TurnState:
    preferences: Preferences
    question: Question | None = None
    itinerary: Itinerary | None = None
    rejected_itineraries: int = 0
    events: list[str] = field(default_factory=list)


def _ok(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _error(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "is_error": True}


def _scrub(value: Any) -> Any:
    """Apply privacy redaction to every string the model hands back to us."""
    if isinstance(value, str):
        return redact_sensitive(value)[0]
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    return value


def make_handlers(state: TurnState) -> dict[str, Any]:
    """Plain async handlers bound to ``state``. Exposed for unit tests."""

    async def update_preferences(args: dict[str, Any]) -> dict[str, Any]:
        args = {k: v for k, v in _scrub(args).items() if k not in APP_CONTROLLED_FIELDS}
        try:
            state.preferences = merge_preferences(state.preferences, args)
        except ValidationError as exc:
            return _error(f"Invalid preferences: {exc.errors()[0]['msg']}")
        state.events.append("preferences")
        return _ok("Preferences saved.")

    async def ask_question(args: dict[str, Any]) -> dict[str, Any]:
        try:
            question = Question.model_validate(_scrub(args))
        except ValidationError as exc:
            return _error(f"Invalid question: {exc.errors()[0]['msg']}")
        if question.key in state.preferences.skipped:
            return _error("The traveler skipped that question. Do not ask it again; assume a sensible default.")
        template = known_question(question.key)
        if template and not question.options:
            question = question.model_copy(update={"options": template.options, "multi_select": template.multi_select})
        state.question = question
        state.events.append("question")
        return _ok("Question will be shown to the traveler.")

    async def submit_itinerary(args: dict[str, Any]) -> dict[str, Any]:
        missing = missing_core(state.preferences)
        if missing:
            state.rejected_itineraries += 1
            keys = ", ".join(q.key for q in missing)
            return _error(f"Not yet: ask the remaining initial questions first ({keys}). The traveler may skip them.")
        if needs_destination_choice(state.preferences):
            state.rejected_itineraries += 1
            return _error("Not yet: suggest 2-3 destinations and let the traveler choose one first.")
        try:
            state.itinerary = validate_itinerary(_scrub(args))
        except ItineraryValidationError as exc:
            state.rejected_itineraries += 1
            return _error(f"Itinerary rejected, please fix and resubmit: {exc}")
        state.events.append("itinerary")
        return _ok("Itinerary saved and shown to the traveler.")

    return {
        "update_preferences": update_preferences,
        "ask_question": ask_question,
        "submit_itinerary": submit_itinerary,
    }


def build_server(state: TurnState):
    handlers = make_handlers(state)
    tools = [
        tool(
            "update_preferences",
            "Record trip details the traveler just shared. Send only fields learned this turn.",
            _PREFERENCE_SCHEMA,
        )(handlers["update_preferences"]),
        tool(
            "ask_question",
            "Show the traveler one question card, optionally with selectable options.",
            _QUESTION_SCHEMA,
        )(handlers["ask_question"]),
        tool(
            "submit_itinerary",
            "Submit the complete day-by-day itinerary (new or revised).",
            _ITINERARY_SCHEMA,
        )(handlers["submit_itinerary"]),
    ]
    return create_sdk_mcp_server(name=SERVER_NAME, version="1.0.0", tools=tools)
