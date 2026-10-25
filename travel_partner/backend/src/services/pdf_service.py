"""Renders a confirmed itinerary to a printable PDF, entirely in memory.

All text goes through ``esc()`` before it reaches ReportLab's Paragraph markup
parser, so itinerary content cannot inject markup (fonts, links, images).
"""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape  # nosec B406 - only the string escaper is used; no XML is parsed

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from agents.travel_planner.schemas import Itinerary, Link

INK = colors.HexColor("#3b2f2a")
ACCENT = colors.HexColor("#c0583a")
MUTED = colors.HexColor("#7a6a5e")
PAPER = colors.HexColor("#f7efe3")

_base = getSampleStyleSheet()
STYLES = {
    "title": ParagraphStyle("title", parent=_base["Title"], textColor=INK, fontSize=24, leading=28),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Normal"], textColor=MUTED, alignment=TA_CENTER, fontSize=11),
    "h2": ParagraphStyle("h2", parent=_base["Heading2"], textColor=ACCENT, spaceBefore=10, spaceAfter=4),
    "h3": ParagraphStyle("h3", parent=_base["Heading4"], textColor=INK, spaceBefore=6, spaceAfter=2),
    "body": ParagraphStyle("body", parent=_base["BodyText"], textColor=INK, fontSize=10, leading=14),
    "small": ParagraphStyle("small", parent=_base["BodyText"], textColor=MUTED, fontSize=8.5, leading=11),
}


def esc(text: object) -> str:
    return escape(str(text))


def _p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def _bullets(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(_p(esc(i)), leftIndent=10) for i in items],
        bulletType="bullet",
        start="•",
        leftIndent=12,
    )


def _link_text(link: Link) -> str:
    # The URL is printed as escaped plain text rather than an <a> tag, so no
    # markup derived from model output is ever interpreted.
    return f"{esc(link.label)}: {esc(link.url)}"


def _meta_table(it: Itinerary) -> Table:
    dates = " – ".join(d for d in (it.start_date, it.end_date) if d) or "Flexible"
    rows = [
        [_p("<b>Destination</b>"), _p(esc(it.destination))],
        [_p("<b>Dates</b>"), _p(esc(dates))],
        [_p("<b>Duration</b>"), _p(f"{it.duration_days} day{'s' if it.duration_days != 1 else ''}")],
    ]
    table = Table(rows, colWidths=[35 * mm, None])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("BOX", (0, 0), (-1, -1), 0.5, MUTED),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _day(day) -> list:
    heading = f"Day {day.day_number}: {esc(day.title)}"
    if day.date:
        heading += f" <font color='#7a6a5e' size='9'>({esc(day.date)})</font>"
    parts: list = [_p(heading, "h2")]
    if day.location:
        parts.append(_p(f"<i>{esc(day.location)}</i>", "small"))
    for act in day.activities:
        line = f"<b>{esc(act.time_of_day + ': ') if act.time_of_day else ''}{esc(act.name)}</b>"
        details = [esc(x) for x in (act.location, act.duration, act.est_cost) if x]
        if details:
            line += f" <font color='#7a6a5e'>({' · '.join(details)})</font>"
        parts.append(_p(line))
        if act.description:
            parts.append(_p(esc(act.description), "small"))
        if act.link:
            parts.append(_p(_link_text(act.link), "small"))
    if day.travel:
        parts.append(_p("Getting around", "h3"))
        parts.append(
            _bullets(
                [
                    f"{leg.origin} → {leg.destination}"
                    + "".join(f", {x}" for x in (leg.mode, leg.est_duration, leg.est_distance) if x)
                    for leg in day.travel
                ]
            )
        )
    if day.lodging:
        parts.append(_p("Stay", "h3"))
        lodging = day.lodging
        text = f"<b>{esc(lodging.name)}</b>"
        if lodging.est_cost:
            text += f" ({esc(lodging.est_cost)})"
        parts.append(_p(text))
        if lodging.description:
            parts.append(_p(esc(lodging.description), "small"))
    if day.restaurants:
        parts.append(_p("Where to eat", "h3"))
        parts.append(_bullets([r.name + (f" ({r.est_cost})" if r.est_cost else "") for r in day.restaurants]))
    if day.notes:
        parts.append(_bullets(day.notes))
    return [KeepTogether(parts[:3]), *parts[3:]]


def render_itinerary_pdf(it: Itinerary, version: int) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=it.title[:120],
        author="Travel Partner",
    )
    story: list = [
        _p(esc(it.title), "title"),
        _p(f"Confirmed itinerary · version {version}", "subtitle"),
        Spacer(1, 6 * mm),
        _meta_table(it),
    ]
    if it.summary:
        story += [Spacer(1, 4 * mm), _p(esc(it.summary))]
    for day in it.days:
        story += [Spacer(1, 3 * mm), HRFlowable(width="100%", color=PAPER, thickness=1.2), *_day(day)]

    if it.budget:
        story.append(_p("Estimated budget", "h2"))
        rows = [[_p(f"<b>{esc(i.category)}</b>"), _p(esc(i.amount))] for i in it.budget.items]
        if it.budget.total:
            rows.append([_p("<b>Total (estimate)</b>"), _p(f"<b>{esc(it.budget.total)}</b>")])
        if rows:
            table = Table(rows, colWidths=[60 * mm, None])
            table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, MUTED)]))
            story.append(table)
        if it.budget.assumptions:
            story += [_p("Assumptions", "h3"), _bullets(it.budget.assumptions)]

    if it.booking_links:
        links = [f"{link.label}: {link.url}" for link in it.booking_links]
        story += [_p("Booking and useful links", "h2"), _bullets(links)]
    if it.travel_notes:
        story += [_p("Travel notes", "h2"), _bullets(it.travel_notes)]
    caveats = [
        *it.caveats,
        "Prices, opening hours, availability and conditions are estimates or unverified unless "
        "stated otherwise. Check with providers before you travel. No bookings have been made.",
    ]
    story += [_p("Caveats", "h2"), _bullets(caveats)]

    doc.build(story)
    return buffer.getvalue()
