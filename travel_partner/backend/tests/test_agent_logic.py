"""Questionnaire, tool handlers, itinerary validation and refinement context (no API calls)."""

import pytest

from agents.travel_planner.agent import TurnInput, build_prompt
from agents.travel_planner.questionnaire import (
    mark_skipped,
    merge_preferences,
    missing_core,
    ready_to_generate,
    relevant_follow_ups,
)
from agents.travel_planner.schemas import Itinerary, Preferences
from agents.travel_planner.tools import TurnState, make_handlers
from agents.travel_planner.validation import ItineraryValidationError, redact_sensitive, validate_itinerary

from .conftest import ALL_CORE_ANSWERS, sample_itinerary


def keys(questions):
    return [q.key for q in questions]


def test_all_core_questions_open_at_start():
    assert keys(missing_core(Preferences())) == [
        "destination",
        "travel_dates",
        "duration_days",
        "travelers",
        "budget",
        "interests",
    ]
    assert not ready_to_generate(Preferences())


def test_answered_and_skipped_questions_are_not_reasked():
    prefs = Preferences(destination="Iceland", duration_days=7)
    prefs = mark_skipped(prefs, "budget")
    remaining = keys(missing_core(prefs))
    assert "destination" not in remaining and "duration_days" not in remaining and "budget" not in remaining
    assert not ready_to_generate(prefs)  # travel_dates, travelers and interests are still open


def test_wants_suggestions_counts_as_destination_answer():
    assert "destination" not in keys(missing_core(Preferences(wants_suggestions=True)))


def test_mark_skipped_ignores_unknown_keys():
    assert mark_skipped(Preferences(), "not_a_question").skipped == []


def test_follow_ups_only_when_relevant():
    assert relevant_follow_ups(Preferences(interests=["cities"])) == []
    road = keys(relevant_follow_ups(Preferences(interests=["scenic_drives", "hiking", "food"])))
    assert road == ["departure_location", "driving_preference", "activity_level", "dietary"]
    answered = Preferences(interests=["scenic_drives"], departure_location="Denver", driving_preference="<3h")
    assert relevant_follow_ups(answered) == []
    assert keys(relevant_follow_ups(Preferences(is_international=True))) == ["nationality"]


def test_merge_unions_lists_and_keeps_values():
    prefs = Preferences(destination="Utah", interests=["hiking"])
    merged = merge_preferences(
        prefs, {"interests": ["hiking", "photography"], "destination": None, "duration_days": 5, "bogus": 1}
    )
    assert merged.destination == "Utah" and merged.duration_days == 5
    assert merged.interests == ["hiking", "photography"]


def test_merge_rejects_invalid_values():
    with pytest.raises(ValueError):
        merge_preferences(Preferences(), {"duration_days": 500})
    with pytest.raises(ValueError):
        merge_preferences(Preferences(), {"interests": ["skydiving"]})


async def test_update_preferences_tool_parses_multiple_answers():
    state = TurnState(preferences=Preferences())
    handlers = make_handlers(state)
    res = await handlers["update_preferences"](
        {
            "destination": "Banff",
            "duration_days": 4,
            "travelers": "couple",
            "interests": ["lakes", "hiking"],
            "skipped": ["destination"],
        }
    )
    assert "is_error" not in res
    p = state.preferences
    assert (p.destination, p.duration_days, p.travelers) == ("Banff", 4, "couple")
    assert p.skipped == []  # the model cannot mark questions skipped


async def test_update_preferences_tool_reports_invalid_input():
    state = TurnState(preferences=Preferences())
    res = await make_handlers(state)["update_preferences"]({"duration_days": -3})
    assert res["is_error"] is True and state.preferences.duration_days is None


async def test_tool_redacts_sensitive_strings():
    state = TurnState(preferences=Preferences())
    await make_handlers(state)["update_preferences"]({"notes": ["passport number AB1234567"]})
    assert "AB1234567" not in str(state.preferences.notes)


async def test_ask_question_fills_default_options_and_blocks_skipped():
    state = TurnState(preferences=mark_skipped(Preferences(), "budget"))
    h = make_handlers(state)
    res = await h["ask_question"]({"key": "budget", "text": "Budget?"})
    assert res["is_error"] is True and state.question is None
    await h["ask_question"]({"key": "interests", "text": "What do you love?"})
    assert state.question.multi_select and "Hiking" in state.question.options


async def test_submit_itinerary_validates():
    state = TurnState(preferences=Preferences(**ALL_CORE_ANSWERS))
    h = make_handlers(state)
    bad = sample_itinerary(2)
    bad["duration_days"] = 3
    res = await h["submit_itinerary"](bad)
    assert res["is_error"] is True and state.itinerary is None and state.rejected_itineraries == 1
    res = await h["submit_itinerary"](sample_itinerary(2))
    assert "is_error" not in res and state.itinerary.duration_days == 2


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["days"].reverse(),
        lambda d: d.update(days=[]),
        lambda d: d["booking_links"].append({"label": "x", "url": "javascript:alert(1)"}),
        lambda d: d.update(unexpected="field"),
        lambda d: d.update(title="x" * 400),
    ],
)
def test_validate_itinerary_rejects_bad_output(mutate):
    data = sample_itinerary(2)
    mutate(data)
    with pytest.raises(ItineraryValidationError):
        validate_itinerary(data)


def test_redaction_leaves_ordinary_text_alone():
    text = "Trip on 2026-05-10 for 2 people, budget $3000, call +1 555 123 4567, passport is Canadian"
    assert redact_sensitive(text) == (text, False)


def test_refinement_prompt_includes_current_itinerary():
    it = Itinerary.model_validate(sample_itinerary(2))
    turn = TurnInput(
        message="less driving",
        preferences=Preferences(destination="Utah"),
        history=[],
        itinerary=it,
        itinerary_version=3,
        confirmed=False,
    )
    prompt = build_prompt(turn)
    assert 'version="3"' in prompt and "Utah Canyon Escape" in prompt and "less driving" in prompt
    assert "Build the itinerary" not in prompt


def test_generation_prompt_when_ready():
    prefs = Preferences(
        destination="Utah", duration_days=3, travel_dates="May", travelers="2", budget="mid", interests=["cities"]
    )
    prompt = build_prompt(
        TurnInput(message="go", preferences=prefs, history=[], itinerary=None, itinerary_version=None, confirmed=False)
    )
    assert "Build the itinerary this turn" in prompt
    assert "(none: everything essential" in prompt


@pytest.mark.parametrize(
    ("status", "detail", "expected"),
    [
        (400, "Credit balance is too low", "no credits"),
        (401, "Invalid API key", "rejected the API key"),
        (529, "Overloaded", "busy"),
        (None, "secret internal detail", "unavailable"),
    ],
)
def test_account_errors_map_to_fixed_messages(status, detail, expected):
    from agents.travel_planner.agent import _account_error_message

    message = _account_error_message(status, detail)
    assert expected in message and detail not in message
