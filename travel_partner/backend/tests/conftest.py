from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from agents.travel_planner.agent import TurnInput, TurnResult
from agents.travel_planner.questionnaire import merge_preferences
from agents.travel_planner.schemas import Itinerary
from src.app import create_app
from src.config import Settings
from src.middleware.rate_limit import limiter

ORIGIN = "http://localhost:5173"

# Answers to all six initial questions, as the model would record them.
ALL_CORE_ANSWERS = {
    "destination": "Southern Utah",
    "travel_dates": "May 2026",
    "duration_days": 2,
    "travelers": "2 adults",
    "budget": "mid-range",
    "interests": ["hiking"],
}


def sample_itinerary(days: int = 2, title: str = "Utah Canyon Escape") -> dict:
    return {
        "title": title,
        "destination": "Southern Utah",
        "start_date": "2026-05-10",
        "end_date": f"2026-05-{9 + days}",
        "duration_days": days,
        "summary": "Red rock canyons at a relaxed pace.",
        "days": [
            {
                "day_number": i,
                "title": f"Day {i} in the canyons",
                "location": "Springdale, UT",
                "activities": [
                    {
                        "time_of_day": "Morning",
                        "name": "Riverside Walk",
                        "duration": "2 hours",
                        "est_cost": "Park pass ~$35/vehicle (estimate)",
                        "link": {"label": "NPS", "url": "https://www.nps.gov/zion/"},
                    }
                ],
                "travel": [
                    {
                        "origin": "Las Vegas",
                        "destination": "Springdale",
                        "est_duration": "2h45m",
                        "est_distance": "260 km",
                    }
                ],
                "lodging": {"name": "Cabin near the park", "est_cost": "~$180/night (estimate)"},
                "restaurants": [{"name": "Local café"}],
            }
            for i in range(1, days + 1)
        ],
        "budget": {
            "currency": "USD",
            "items": [{"category": "Lodging", "amount": "~$360"}],
            "total": "~$900",
            "assumptions": ["2 travelers"],
        },
        "booking_links": [{"label": "Zion NP", "url": "https://www.nps.gov/zion/"}],
        "caveats": ["Check flash flood warnings before canyon hikes."],
    }


class FakeAgent:
    """Scripted stand-in for the model. Mimics what the real tools would record."""

    def __init__(self) -> None:
        self.turns: list[TurnInput] = []
        self.next_preferences: dict | None = None
        self.next_itinerary: dict | None = None
        self.next_reply = "Sounds lovely!"
        self.delay: float = 0
        self.fail: Exception | None = None

    async def run_turn(self, turn: TurnInput) -> TurnResult:
        import asyncio

        self.turns.append(turn)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail:
            raise self.fail
        prefs = turn.preferences
        if self.next_preferences:
            prefs = merge_preferences(prefs, self.next_preferences)
        itinerary = Itinerary.model_validate(self.next_itinerary) if self.next_itinerary else None
        self.next_preferences = self.next_itinerary = None
        return TurnResult(reply=self.next_reply, preferences=prefs, question=None, itinerary=itinerary)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        anthropic_api_key=SecretStr("test-key-not-a-real-anthropic-key-000000"),
        allowed_origins=ORIGIN,
        agent_timeout_seconds=1,
        max_messages_per_session=6,
    )


@pytest.fixture
def agent() -> FakeAgent:
    return FakeAgent()


@pytest.fixture
def client(settings: Settings, agent: FakeAgent):
    limiter.reset()
    app = create_app(settings=settings, agent=agent)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    limiter.reset()


@pytest.fixture
def session(client: TestClient) -> dict:
    res = client.post("/api/sessions")
    assert res.status_code == 201
    sid = res.json()["session_id"]
    return {"X-Session-Id": sid}
