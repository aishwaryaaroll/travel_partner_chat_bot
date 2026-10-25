"""Request validation, limits and error handling."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from agents.travel_planner.agent import AgentError
from src.app import create_app


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 2001},
        {"message": 42},
        {"message": "hi", "extra": "field"},
        {"message": "hi", "skip_question": "../etc/passwd"},
    ],
)
def test_invalid_chat_bodies_rejected(client, session, payload):
    res = client.post("/api/chat", json=payload, headers=session)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "invalid_request"
    assert "x" * 50 not in res.text  # submitted values are not echoed


@pytest.mark.parametrize("sid", [None, "short", "has spaces in it which is bad!!", "a" * 100])
def test_bad_or_missing_session_header(client, sid):
    headers = {"X-Session-Id": sid} if sid else {}
    res = client.post("/api/chat", json={"message": "hi"}, headers=headers)
    assert res.status_code == 422


def test_unknown_session_is_404(client):
    res = client.post("/api/chat", json={"message": "hi"}, headers={"X-Session-Id": "A" * 43})
    assert res.status_code == 404 and res.json()["error"]["code"] == "session_not_found"


def test_body_size_limit(client, session):
    res = client.post(
        "/api/chat",
        content=b'{"message":"' + b"a" * 20000 + b'"}',
        headers={**session, "Content-Type": "application/json"},
    )
    assert res.status_code == 413


def test_invalid_json(client, session):
    res = client.post("/api/chat", content=b"{not json", headers={**session, "Content-Type": "application/json"})
    assert res.status_code == 422


def test_conversation_turn_limit(client, session):
    # max_messages_per_session=6 in tests → 3 exchanges; the greeting uses part of the budget.
    codes = [client.post("/api/chat", json={"message": f"msg {i}"}, headers=session).status_code for i in range(4)]
    assert codes[-1] == 429


def test_agent_timeout_returns_504(client, session, agent):
    agent.delay = 2  # timeout is 1s in tests
    res = client.post("/api/chat", json={"message": "hi"}, headers=session)
    assert res.status_code == 504 and res.json()["error"]["code"] == "agent_timeout"


def test_agent_failure_hides_internals(client, session, agent):
    agent.fail = AgentError("The travel agent is unavailable right now.")
    res = client.post("/api/chat", json={"message": "hi"}, headers=session)
    assert res.status_code == 502
    assert "Traceback" not in res.text


def test_unexpected_exception_is_generic_500(client, session, agent):
    agent.fail = RuntimeError("secret internal detail /home/app/config.py")
    res = client.post("/api/chat", json={"message": "hi"}, headers=session)
    assert res.status_code == 500
    assert "secret internal detail" not in res.text and "config.py" not in res.text
    assert res.json()["error"]["code"] == "internal_error"


def test_concurrent_message_rejected(settings, agent):
    agent.delay = 0.5

    async def run():
        import httpx

        app = create_app(settings=settings, agent=agent)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            sid = (await c.post("/api/sessions")).json()["session_id"]
            h = {"X-Session-Id": sid}
            return await asyncio.gather(
                c.post("/api/chat", json={"message": "one"}, headers=h),
                c.post("/api/chat", json={"message": "two"}, headers=h),
            )

    from src.middleware.rate_limit import limiter

    limiter.reset()
    codes = sorted(r.status_code for r in asyncio.run(run()))
    assert codes == [200, 409]


def test_unknown_route_and_no_docs(client):
    for path in ("/nope", "/docs", "/openapi.json"):
        res = client.get(path)
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "not_found"


def test_agent_not_configured(settings):
    from pydantic import SecretStr

    settings.anthropic_api_key = SecretStr("")
    with TestClient(create_app(settings=settings), raise_server_exceptions=False) as c:
        sid = c.post("/api/sessions").json()["session_id"]
        res = c.post("/api/chat", json={"message": "hi"}, headers={"X-Session-Id": sid})
        assert res.status_code == 503 and res.json()["error"]["code"] == "agent_not_configured"
        assert c.get("/api/health").json() == {"status": "ok", "agent_configured": False}
