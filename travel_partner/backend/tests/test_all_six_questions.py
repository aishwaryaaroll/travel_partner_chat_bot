"""All six initial questions must be asked (each skippable) before suggestions or an itinerary."""

import pytest

from agents.travel_planner.agent import TurnInput, build_prompt
from agents.travel_planner.questionnaire import (
    CORE_QUESTIONS,
    mark_answered,
    mark_skipped,
    merge_preferences,
    missing_core,
    needs_destination_choice,
    ready_to_generate,
)
from agents.travel_planner.schemas import Preferences
from agents.travel_planner.tools import _PREFERENCE_SCHEMA, TurnState, make_handlers

from .conftest import ALL_CORE_ANSWERS, sample_itinerary

CORE_KEYS = [q.key for q in CORE_QUESTIONS]


def prompt_for(prefs: Preferences) -> str:
    turn = TurnInput(
        message="hi", preferences=prefs, history=[], itinerary=None, itinerary_version=None, confirmed=False
    )
    return build_prompt(turn)


# ---------- questionnaire rules ----------


@pytest.mark.parametrize("left_open", CORE_KEYS)
def test_not_ready_while_any_core_question_is_open(left_open):
    answers = {k: v for k, v in ALL_CORE_ANSWERS.items() if k != left_open}
    prefs = Preferences(**answers)
    assert [q.key for q in missing_core(prefs)] == [left_open]
    assert not ready_to_generate(prefs)


def test_ready_when_all_six_answered_or_skipped():
    prefs = Preferences(destination="Iceland", duration_days=7)
    for key in ("travel_dates", "travelers", "budget", "interests"):
        assert not ready_to_generate(prefs)
        prefs = mark_skipped(prefs, key)
    assert ready_to_generate(prefs)


def test_card_answer_marks_question_answered_even_if_model_records_nothing():
    prefs = mark_answered(Preferences(), "travelers")
    assert "travelers" not in [q.key for q in missing_core(prefs)]
    assert mark_answered(prefs, "travelers").answered == ["travelers"]  # idempotent
    assert mark_answered(prefs, "not_a_question").answered == ["travelers"]


def test_model_cannot_set_app_controlled_fields():
    merged = merge_preferences(Preferences(), {"answered": CORE_KEYS, "skipped": CORE_KEYS, "budget": "low"})
    assert merged.answered == [] and merged.skipped == [] and merged.budget == "low"
    assert "answered" not in _PREFERENCE_SCHEMA["properties"]
    assert "skipped" not in _PREFERENCE_SCHEMA["properties"]


def test_suggestions_wait_for_a_destination_choice():
    prefs = Preferences(**{**ALL_CORE_ANSWERS, "destination": None, "wants_suggestions": True})
    assert ready_to_generate(prefs) and needs_destination_choice(prefs)
    assert not needs_destination_choice(prefs.model_copy(update={"destination": "Banff"}))


# ---------- prompt guidance ----------


def test_hint_asks_next_open_question_and_forbids_itinerary():
    prompt = prompt_for(Preferences(destination="Utah", duration_days=3))
    assert "Ask the next open core question: travel_dates" in prompt
    assert "Do not suggest destinations or build the itinerary yet" in prompt


def test_hint_requests_suggestions_based_on_all_six():
    prefs = Preferences(**{**ALL_CORE_ANSWERS, "destination": None, "wants_suggestions": True})
    prompt = prompt_for(prefs)
    assert "Propose 2-3 destinations that fit all six answers" in prompt


def test_hint_builds_when_all_six_settled():
    assert "Build the itinerary this turn using all six answers" in prompt_for(Preferences(**ALL_CORE_ANSWERS))


# ---------- tool guard ----------


async def test_submit_itinerary_rejected_until_all_six_settled():
    state = TurnState(preferences=Preferences(destination="Utah", duration_days=2))
    res = await make_handlers(state)["submit_itinerary"](sample_itinerary(2))
    assert res["is_error"] is True and state.itinerary is None
    assert "travel_dates" in res["content"][0]["text"]


async def test_submit_itinerary_rejected_until_destination_chosen():
    prefs = Preferences(**{**ALL_CORE_ANSWERS, "destination": None, "wants_suggestions": True})
    state = TurnState(preferences=prefs)
    res = await make_handlers(state)["submit_itinerary"](sample_itinerary(2))
    assert res["is_error"] is True and "destinations" in res["content"][0]["text"]


# ---------- API behaviour ----------


def test_cards_walk_through_all_six_in_order(client, session, agent, settings):
    settings.max_messages_per_session = 40  # the shared test default (6) is too small for six turns
    seen = [client.get("/api/session", headers=session).json()["question"]["key"]]
    for _ in range(5):
        body = client.post("/api/chat", json={"message": "some answer", "answering": seen[-1]}, headers=session).json()
        seen.append(body["question"]["key"])
        assert body["ready_to_generate"] is False
    assert seen == CORE_KEYS


def test_premature_itinerary_from_model_is_discarded(client, session, agent):
    agent.next_preferences = {"destination": "Utah", "duration_days": 2}
    agent.next_itinerary = sample_itinerary(2)
    body = client.post("/api/chat", json={"message": "2 days in Utah, just plan it"}, headers=session).json()
    assert body["itinerary"]["version"] is None and body["stage"] == "gathering"
    assert body["question"]["key"] == "travel_dates"
    assert body["open_core_questions"] == 4


def test_state_reports_ready_after_last_question(client, session, agent):
    agent.next_preferences = dict(ALL_CORE_ANSWERS)
    body = client.post("/api/chat", json={"message": "everything at once"}, headers=session).json()
    assert body["ready_to_generate"] is True and body["open_core_questions"] == 0
    assert body["awaiting_destination_choice"] is False


@pytest.mark.parametrize("bad", ["../x", "Budget", "a" * 41, "drop table"])
def test_answering_field_is_validated(client, session, bad):
    res = client.post("/api/chat", json={"message": "hi", "answering": bad}, headers=session)
    assert res.status_code == 422
