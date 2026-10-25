"""Data shapes shared by the agent and the backend.

Every model forbids unknown fields and caps string and list sizes, so a
misbehaving model or client cannot smuggle large or unexpected data through.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1500)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Interest(str, Enum):
    mountains = "mountains"
    lakes = "lakes"
    waterfalls = "waterfalls"
    beaches = "beaches"
    scenic_drives = "scenic_drives"
    hiking = "hiking"
    cities = "cities"
    food = "food"
    culture = "culture"
    relaxation = "relaxation"
    photography = "photography"


class Preferences(Strict):
    """What we know about the trip so far. Contains no identity data by design."""

    destination: ShortText | None = None
    wants_suggestions: bool | None = None
    travel_dates: ShortText | None = None
    duration_days: int | None = Field(default=None, ge=1, le=60)
    travelers: ShortText | None = None
    budget: ShortText | None = None
    interests: list[Interest] = Field(default_factory=list, max_length=11)
    departure_location: ShortText | None = None
    driving_preference: ShortText | None = None
    activity_level: ShortText | None = None
    accommodation: ShortText | None = None
    dietary: ShortText | None = None
    must_see: list[ShortText] = Field(default_factory=list, max_length=20)
    avoid: list[ShortText] = Field(default_factory=list, max_length=20)
    is_international: bool | None = None
    nationality: ShortText | None = None
    notes: list[ShortText] = Field(default_factory=list, max_length=20)
    skipped: list[ShortText] = Field(default_factory=list, max_length=30)
    # Questions the traveler replied to via their question card. Set only by the app.
    answered: list[ShortText] = Field(default_factory=list, max_length=30)


class Link(Strict):
    label: ShortText
    url: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]

    @field_validator("url")
    @classmethod
    def http_only(cls, value: str) -> str:
        if not value.lower().startswith(("https://", "http://")):
            raise ValueError("links must use http or https")
        return value


class Place(Strict):
    name: ShortText
    description: LongText | None = None
    location: ShortText | None = None
    est_cost: ShortText | None = None
    url: Link | None = None


class Activity(Strict):
    time_of_day: ShortText | None = None
    name: ShortText
    description: LongText | None = None
    location: ShortText | None = None
    duration: ShortText | None = None
    est_cost: ShortText | None = None
    link: Link | None = None


class TravelLeg(Strict):
    origin: ShortText
    destination: ShortText
    mode: ShortText | None = None
    est_duration: ShortText | None = None
    est_distance: ShortText | None = None


class Day(Strict):
    day_number: int = Field(ge=1, le=60)
    date: ShortText | None = None
    title: ShortText
    location: ShortText | None = None
    activities: list[Activity] = Field(default_factory=list, max_length=12)
    travel: list[TravelLeg] = Field(default_factory=list, max_length=8)
    lodging: Place | None = None
    restaurants: list[Place] = Field(default_factory=list, max_length=6)
    notes: list[ShortText] = Field(default_factory=list, max_length=8)


class BudgetItem(Strict):
    category: ShortText
    amount: ShortText


class Budget(Strict):
    currency: ShortText | None = None
    items: list[BudgetItem] = Field(default_factory=list, max_length=20)
    total: ShortText | None = None
    assumptions: list[ShortText] = Field(default_factory=list, max_length=12)


class Itinerary(Strict):
    title: ShortText
    destination: ShortText
    start_date: ShortText | None = None
    end_date: ShortText | None = None
    duration_days: int = Field(ge=1, le=60)
    summary: LongText | None = None
    days: list[Day] = Field(min_length=1, max_length=60)
    budget: Budget | None = None
    booking_links: list[Link] = Field(default_factory=list, max_length=20)
    travel_notes: list[ShortText] = Field(default_factory=list, max_length=20)
    caveats: list[ShortText] = Field(default_factory=list, max_length=20)


class Question(Strict):
    key: ShortText
    text: ShortText
    options: list[ShortText] = Field(default_factory=list, max_length=15)
    multi_select: bool = False
    optional: bool = True
