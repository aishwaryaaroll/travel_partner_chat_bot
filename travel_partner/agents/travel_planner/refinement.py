"""Context for refining an existing itinerary."""

from __future__ import annotations

from .schemas import Itinerary

# Quick-change chips offered by the UI. The text is sent as an ordinary traveler message.
QUICK_REFINEMENTS: dict[str, str] = {
    "less_driving": "Please reduce the amount of driving.",
    "more_nature": "Please add more nature and outdoor time.",
    "lower_budget": "Please bring the overall cost down.",
    "more_relaxed": "Please make the schedule more relaxed.",
}


def itinerary_section(itinerary: Itinerary | None, version: int | None, confirmed: bool) -> str:
    if itinerary is None:
        return "<current_itinerary>(none yet)</current_itinerary>"
    status = "confirmed by the traveler" if confirmed else "draft"
    return "\n".join(
        [
            f'<current_itinerary version="{version}" status="{status}">',
            itinerary.model_dump_json(exclude_none=True),
            "</current_itinerary>",
            "<guidance>An itinerary exists. If the traveler asks for changes, submit the full "
            "revised itinerary and summarize what changed in one or two sentences. If they only "
            "ask a question, answer it without resubmitting.</guidance>",
        ]
    )
