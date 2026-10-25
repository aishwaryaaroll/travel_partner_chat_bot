"""Deterministic questionnaire logic.

The model decides how to phrase things, but which questions are still open is
computed here from the preference state, so already-answered or skipped
questions are never put back on the table.
"""

from __future__ import annotations

from .schemas import Interest, Preferences, Question

INTEREST_LABELS: dict[Interest, str] = {
    Interest.mountains: "Mountains",
    Interest.lakes: "Lakes",
    Interest.waterfalls: "Waterfalls",
    Interest.beaches: "Beaches",
    Interest.scenic_drives: "Scenic drives",
    Interest.hiking: "Hiking",
    Interest.cities: "Cities",
    Interest.food: "Food",
    Interest.culture: "Culture",
    Interest.relaxation: "Relaxation",
    Interest.photography: "Photography",
}

CORE_QUESTIONS: list[Question] = [
    Question(
        key="destination",
        text="Where would you like to go? Or would you like me to suggest a few places?",
        options=["Suggest destinations for me"],
        optional=False,
    ),
    Question(
        key="travel_dates",
        text="When do you want to travel?",
        options=["This month", "Next month", "In 2–3 months", "I'm flexible"],
    ),
    Question(
        key="duration_days",
        text="How long is the trip?",
        options=["A weekend (2–3 days)", "About a week", "10–14 days"],
        optional=False,
    ),
    Question(
        key="travelers",
        text="Who is traveling?",
        options=["Just me", "A couple", "Family with kids", "Group of friends"],
    ),
    Question(
        key="budget",
        text="What's your approximate budget?",
        options=["Budget-friendly", "Mid-range", "Comfortable", "Luxury"],
    ),
    Question(
        key="interests",
        text="What experiences do you enjoy most? Pick as many as you like.",
        options=list(INTEREST_LABELS.values()),
        multi_select=True,
    ),
]

FOLLOW_UP_QUESTIONS: dict[str, Question] = {
    "departure_location": Question(
        key="departure_location",
        text="Where will you be starting from? It helps me plan the route.",
    ),
    "driving_preference": Question(
        key="driving_preference",
        text="How do you feel about driving each day?",
        options=["Keep it under 2 hours", "Up to 4 hours is fine", "Long drives are part of the fun"],
    ),
    "activity_level": Question(
        key="activity_level",
        text="What activity level suits you?",
        options=["Easy and relaxed", "Moderate", "Challenging hikes welcome"],
    ),
    "accommodation": Question(
        key="accommodation",
        text="What kind of places do you like to stay in?",
        options=["Hotels", "Cabins / lodges", "Campsites", "Vacation rentals", "No preference"],
    ),
    "dietary": Question(
        key="dietary",
        text="Any dietary requirements I should keep in mind for restaurants?",
        options=["None", "Vegetarian", "Vegan", "Gluten-free"],
    ),
    "must_see": Question(
        key="must_see",
        text="Any must-see places, or anything you'd rather avoid?",
    ),
    "nationality": Question(
        key="nationality",
        text=(
            "Which country issued your passport? I only need the country, not the number, to check entry requirements."
        ),
    ),
}

_OUTDOOR = {Interest.hiking, Interest.mountains, Interest.waterfalls, Interest.lakes}


def _answered(prefs: Preferences, key: str) -> bool:
    if key in prefs.skipped or key in prefs.answered:
        return True
    if key == "destination":
        return bool(prefs.destination) or prefs.wants_suggestions is True
    if key == "must_see":
        return bool(prefs.must_see or prefs.avoid)
    value = getattr(prefs, key)
    return bool(value) if isinstance(value, list) else value is not None


def missing_core(prefs: Preferences) -> list[Question]:
    """Core questions that have not been answered or skipped yet, in order."""
    return [q for q in CORE_QUESTIONS if not _answered(prefs, q.key)]


def relevant_follow_ups(prefs: Preferences) -> list[Question]:
    """Follow-ups that would materially change the itinerary and are still open."""
    wanted: list[str] = []
    if Interest.scenic_drives in prefs.interests:
        wanted += ["departure_location", "driving_preference"]
    if _OUTDOOR & set(prefs.interests):
        wanted.append("activity_level")
    if Interest.food in prefs.interests:
        wanted.append("dietary")
    if prefs.is_international:
        wanted.append("nationality")
    seen: set[str] = set()
    result = []
    for key in wanted:
        if key not in seen and not _answered(prefs, key):
            seen.add(key)
            result.append(FOLLOW_UP_QUESTIONS[key])
    return result


def ready_to_generate(prefs: Preferences) -> bool:
    """True only when every one of the six core questions was answered or skipped."""
    return not missing_core(prefs)


def needs_destination_choice(prefs: Preferences) -> bool:
    """The traveler asked for suggestions and hasn't picked a destination yet."""
    return prefs.wants_suggestions is True and not prefs.destination and "destination" not in prefs.skipped


def first_question() -> Question:
    return CORE_QUESTIONS[0]


def known_question(key: str) -> Question | None:
    for q in CORE_QUESTIONS:
        if q.key == key:
            return q
    return FOLLOW_UP_QUESTIONS.get(key)


def mark_skipped(prefs: Preferences, key: str) -> Preferences:
    if known_question(key) is None or key in prefs.skipped:
        return prefs
    return prefs.model_copy(update={"skipped": [*prefs.skipped, key]})


def mark_answered(prefs: Preferences, key: str) -> Preferences:
    if known_question(key) is None or key in prefs.answered:
        return prefs
    return prefs.model_copy(update={"answered": [*prefs.answered, key]})


_LIST_FIELDS = {"interests", "must_see", "avoid", "notes"}
# Fields only the app may change; model updates to them are ignored.
APP_CONTROLLED_FIELDS = {"skipped", "answered"}


def merge_preferences(prefs: Preferences, update: dict) -> Preferences:
    """Merge a partial update. List fields are unioned; ``None`` never erases a value."""
    data = prefs.model_dump()
    for key, value in update.items():
        if key not in Preferences.model_fields or key in APP_CONTROLLED_FIELDS or value is None:
            continue
        if key in _LIST_FIELDS:
            existing = data.get(key) or []
            additions = value if isinstance(value, list) else [value]
            data[key] = existing + [v for v in additions if v not in existing]
        else:
            data[key] = value
    return Preferences.model_validate(data)
