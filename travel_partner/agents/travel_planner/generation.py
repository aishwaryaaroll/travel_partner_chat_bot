"""Builds the per-turn context that drives questioning and itinerary generation."""

from __future__ import annotations

import json

from .questionnaire import missing_core, needs_destination_choice, relevant_follow_ups
from .schemas import Itinerary, Preferences

MAX_HISTORY_MESSAGES = 10
MAX_HISTORY_CHARS = 800


def neutralize(text: str) -> str:
    """Stop untrusted text from opening or closing our prompt tags."""
    return text.replace("<", "&lt;").replace(">", "&gt;")


def _history_block(history: list[dict]) -> str:
    lines = []
    for msg in history[-MAX_HISTORY_MESSAGES:]:
        role = "traveler" if msg["role"] == "user" else "you"
        content = msg["content"]
        if len(content) > MAX_HISTORY_CHARS:
            content = content[:MAX_HISTORY_CHARS] + "…"
        lines.append(f"{role}: {neutralize(content)}")
    return "\n".join(lines) or "(none yet)"


def _open_questions_block(prefs: Preferences) -> str:
    core = missing_core(prefs)
    follow = relevant_follow_ups(prefs)
    lines = [f"- {q.key} (core{'' if q.optional else ', needed'}): {q.text}" for q in core]
    lines += [f"- {q.key} (follow-up, optional): {q.text}" for q in follow]
    return "\n".join(lines) or "(none: everything essential is known or skipped)"


def generation_hint(prefs: Preferences, itinerary: Itinerary | None) -> str:
    if itinerary is not None:
        return ""
    missing = missing_core(prefs)
    if missing:
        return (
            f"Ask the next open core question: {missing[0].key}. "
            "Do not suggest destinations or build the itinerary yet; all six initial questions come first."
        )
    if needs_destination_choice(prefs):
        return (
            "All six initial questions are settled. Propose 2-3 destinations that fit all six answers "
            "and ask the traveler to choose (ask_question with key 'destination'). Do not build the itinerary yet."
        )
    return "All six initial questions are settled. Build the itinerary this turn using all six answers."


def build_state_block(
    prefs: Preferences,
    history: list[dict],
    itinerary: Itinerary | None,
    itinerary_section: str,
) -> str:
    known = prefs.model_dump(mode="json", exclude_defaults=True)
    parts = [
        "<state>",
        "<known_preferences>",
        json.dumps(known, ensure_ascii=False) if known else "{}",
        "</known_preferences>",
        "<open_questions>",
        _open_questions_block(prefs),
        "</open_questions>",
        itinerary_section,
        "<recent_conversation>",
        _history_block(history),
        "</recent_conversation>",
    ]
    hint = generation_hint(prefs, itinerary)
    if hint:
        parts += ["<guidance>", hint, "</guidance>"]
    parts.append("</state>")
    return "\n".join(p for p in parts if p)
