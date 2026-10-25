"""Anonymous, in-memory trip sessions with an idle timeout.

Nothing is written to disk. A session id is a random 256-bit token that acts as
the only credential for that session, so it is sent in a header (never in URLs).
"""

from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass, field

from agents.travel_planner.schemas import Itinerary, Preferences, Question


@dataclass
class Session:
    id: str
    preferences: Preferences = field(default_factory=Preferences)
    messages: list[dict] = field(default_factory=list)
    versions: list[Itinerary] = field(default_factory=list)
    confirmed_version: int | None = None
    pending_question: Question | None = None
    last_seen: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def latest_version(self) -> int | None:
        return len(self.versions) or None

    @property
    def latest(self) -> Itinerary | None:
        return self.versions[-1] if self.versions else None

    @property
    def confirmed(self) -> Itinerary | None:
        return self.versions[self.confirmed_version - 1] if self.confirmed_version else None


class SessionLimitError(RuntimeError):
    pass


class SessionStore:
    def __init__(self, ttl_seconds: float, max_sessions: int) -> None:
        self._ttl = ttl_seconds
        self._max = max_sessions
        self._sessions: dict[str, Session] = {}

    def _purge(self) -> None:
        now = time.monotonic()
        expired = [sid for sid, s in self._sessions.items() if now - s.last_seen > self._ttl]
        for sid in expired:
            del self._sessions[sid]

    def create(self) -> Session:
        self._purge()
        if len(self._sessions) >= self._max:
            raise SessionLimitError
        session = Session(id=secrets.token_urlsafe(32))
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        self._purge()
        session = self._sessions.get(session_id)
        if session is not None:
            session.last_seen = time.monotonic()
        return session

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def __len__(self) -> int:
        return len(self._sessions)
