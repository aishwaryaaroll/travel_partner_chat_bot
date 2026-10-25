"""Runs one conversational turn of the travel agent with the Claude Agent SDK.

Each turn is a fresh, stateless ``query()``: the app supplies the state, and
the SDK keeps nothing on disk. The model can use only WebSearch, WebFetch and
our three in-process tools.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

from .generation import build_state_block, neutralize
from .refinement import itinerary_section
from .schemas import Itinerary, Preferences, Question
from .tools import ALLOWED_MCP_TOOLS, SERVER_NAME, TurnState, build_server

log = logging.getLogger("travel_planner.agent")

INSTRUCTIONS = (Path(__file__).parent / "instructions.md").read_text(encoding="utf-8")

WEB_TOOLS = ["WebSearch", "WebFetch"]
# Belt and braces: the base toolset is already limited to WEB_TOOLS.
BLOCKED_TOOLS = [
    "Bash",
    "BashOutput",
    "KillShell",
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "Glob",
    "Grep",
    "Task",
    "Agent",
    "TodoWrite",
    "Skill",
    "SlashCommand",
    "ExitPlanMode",
]


@dataclass
class TurnInput:
    message: str
    preferences: Preferences
    history: list[dict]
    itinerary: Itinerary | None
    itinerary_version: int | None
    confirmed: bool


@dataclass
class TurnResult:
    reply: str
    preferences: Preferences
    question: Question | None
    itinerary: Itinerary | None


class AgentError(RuntimeError):
    """Safe-to-surface failure category. The message never contains model or user text."""


class TravelAgent(Protocol):
    async def run_turn(self, turn: TurnInput) -> TurnResult: ...


def _loop_supports_subprocesses() -> bool:
    if sys.platform != "win32":
        return True
    return isinstance(asyncio.get_running_loop(), asyncio.ProactorEventLoop)


def _account_error_message(status: int | None, detail: str) -> str:
    """Map API account problems to fixed, operator-friendly messages (never echo ``detail``)."""
    if status == 400 and "credit balance" in detail.lower():
        return "The AI service account has no credits left. Add credits in the Anthropic console and try again."
    if status in (401, 403):
        return "The AI service rejected the API key. Check ANTHROPIC_API_KEY in personal-info/.env."
    if status in (429, 529):
        return "The AI service is busy right now. Please try again in a minute."
    return "The travel agent is unavailable right now."


def build_prompt(turn: TurnInput) -> str:
    section = itinerary_section(turn.itinerary, turn.itinerary_version, turn.confirmed)
    state = build_state_block(turn.preferences, turn.history, turn.itinerary, section)
    return f"{state}\n<traveler_message>\n{neutralize(turn.message)}\n</traveler_message>"


class ClaudeTravelAgent:
    def __init__(
        self,
        api_key: str,
        model: str,
        max_turns: int = 14,
        max_budget_usd: float = 1.0,
        timeout_seconds: float = 240,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_turns = max_turns
        self._max_budget_usd = max_budget_usd
        self._timeout_seconds = timeout_seconds
        # Empty working dir and private config dir: the CLI sees no project files,
        # no user settings or memories, and no stored login.
        self._workdir = tempfile.mkdtemp(prefix="travel_agent_cwd_")
        self._config_dir = tempfile.mkdtemp(prefix="travel_agent_cfg_")

    def _options(self, state: TurnState) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            system_prompt=INSTRUCTIONS,
            model=self._model,
            tools=WEB_TOOLS,
            allowed_tools=[*WEB_TOOLS, *ALLOWED_MCP_TOOLS],
            disallowed_tools=BLOCKED_TOOLS,
            mcp_servers={SERVER_NAME: build_server(state)},
            strict_mcp_config=True,
            permission_mode="dontAsk",
            setting_sources=[],
            cwd=self._workdir,
            max_turns=self._max_turns,
            max_budget_usd=self._max_budget_usd,
            env={"ANTHROPIC_API_KEY": self._api_key, "CLAUDE_CONFIG_DIR": self._config_dir},
            extra_args={"no-session-persistence": None},
        )

    async def run_turn(self, turn: TurnInput) -> TurnResult:
        if _loop_supports_subprocesses():
            return await self._run_turn(turn)
        # Windows selector loops (used by `uvicorn --reload`) cannot spawn the CLI
        # subprocess, so run the turn on a private Proactor loop in a worker thread.
        # The inner timeout makes sure the thread stops even if the caller gives up.
        return await asyncio.to_thread(
            asyncio.run, asyncio.wait_for(self._run_turn(turn), timeout=self._timeout_seconds)
        )

    async def _run_turn(self, turn: TurnInput) -> TurnResult:
        state = TurnState(preferences=turn.preferences)
        texts: list[str] = []
        result: ResultMessage | None = None
        try:
            async for message in query(prompt=build_prompt(turn), options=self._options(state)):
                if isinstance(message, AssistantMessage):
                    texts.extend(b.text for b in message.content if isinstance(b, TextBlock))
                elif isinstance(message, ResultMessage):
                    result = message
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - any SDK/CLI failure: log the type only, never content
            status = getattr(exc, "api_error_status", None)
            log.warning("agent turn failed: %s status=%s", type(exc).__name__, status)
            raise AgentError(_account_error_message(status, str(exc))) from None

        if result is not None and result.is_error and state.itinerary is None and not texts:
            log.warning("agent result error: subtype=%s status=%s", result.subtype, result.api_error_status)
            raise AgentError("The travel agent could not complete that request.")

        reply = (result.result if result and result.result else "\n\n".join(texts)).strip()
        if not reply:
            reply = "Here's your updated plan." if state.itinerary else "Tell me a bit more about your trip."
        return TurnResult(
            reply=reply,
            preferences=state.preferences,
            question=state.question,
            itinerary=state.itinerary,
        )
