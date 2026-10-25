"""End-to-end API flow: questionnaire → itinerary → refinement → confirm → PDF."""

from io import BytesIO

from pypdf import PdfReader

from .conftest import ALL_CORE_ANSWERS, sample_itinerary


def pdf_text(content: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)


def test_new_session_greets_and_asks_first_question(client):
    body = client.post("/api/sessions").json()
    assert body["reply"].startswith("Hi!")
    assert body["question"]["key"] == "destination"
    assert body["stage"] == "gathering"
    assert len(body["session_id"]) >= 40


def test_chat_updates_preferences_from_one_message(client, session, agent):
    agent.next_preferences = {
        "destination": "Utah",
        "duration_days": 5,
        "travelers": "2 adults",
        "interests": ["hiking", "photography"],
    }
    body = client.post(
        "/api/chat", json={"message": "2 of us, 5 days in Utah, love hiking and photos"}, headers=session
    ).json()
    prefs = body["preferences"]
    assert prefs["destination"] == "Utah" and prefs["duration_days"] == 5
    assert set(prefs["interests"]) == {"hiking", "photography"}


def test_skip_marks_question_and_agent_sees_it(client, session, agent):
    client.post("/api/chat", json={"message": "skip", "skip_question": "budget"}, headers=session)
    assert "budget" in agent.turns[-1].preferences.skipped


def test_full_flow_confirm_then_pdf_uses_confirmed_version(client, session, agent):
    agent.next_preferences = dict(ALL_CORE_ANSWERS)
    agent.next_itinerary = sample_itinerary(2, title="First Draft Trip")
    body = client.post("/api/chat", json={"message": "plan it"}, headers=session).json()
    assert body["stage"] == "drafting" and body["itinerary"]["version"] == 1

    # PDF is refused before confirmation.
    assert client.get("/api/itinerary/pdf", headers=session).status_code == 409

    agent.next_itinerary = sample_itinerary(3, title="Relaxed Revised Trip")
    body = client.post("/api/chat", json={"message": "more relaxed please"}, headers=session).json()
    assert body["itinerary"]["version"] == 2
    assert agent.turns[-1].itinerary.title == "First Draft Trip"  # refinement sees the current plan

    # Confirming a stale version is refused.
    assert client.post("/api/itinerary/confirm", json={"version": 1}, headers=session).status_code == 409
    body = client.post("/api/itinerary/confirm", json={"version": 2}, headers=session).json()
    assert body["stage"] == "confirmed" and body["itinerary"]["confirmed_version"] == 2

    res = client.get("/api/itinerary/pdf", headers=session)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert 'filename="travel-itinerary.pdf"' in res.headers["content-disposition"]
    text = pdf_text(res.content)
    assert "Relaxed Revised Trip" in text and "First Draft Trip" not in text

    # A newer unconfirmed draft does not change the downloaded PDF.
    agent.next_itinerary = sample_itinerary(2, title="Unconfirmed Third Draft")
    body = client.post("/api/chat", json={"message": "lower budget"}, headers=session).json()
    assert body["stage"] == "drafting"
    text = pdf_text(client.get("/api/itinerary/pdf", headers=session).content)
    assert "Relaxed Revised Trip" in text and "Unconfirmed Third Draft" not in text


def test_confirm_without_itinerary(client, session):
    res = client.post("/api/itinerary/confirm", json={"version": 1}, headers=session)
    assert res.status_code == 409 and res.json()["error"]["code"] == "no_itinerary"


def test_get_and_delete_session(client, session):
    assert client.get("/api/session", headers=session).status_code == 200
    assert client.delete("/api/session", headers=session).status_code == 204
    assert client.get("/api/session", headers=session).status_code == 404
