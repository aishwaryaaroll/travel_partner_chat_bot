# Architecture

## Overview

```
Browser (React + Vite)                Backend (FastAPI)                         Agent (claude-agent-sdk)
┌──────────────────────┐  JSON/HTTPS  ┌───────────────────────────────┐  query()  ┌──────────────────────────┐
│ pages / components   │ ───────────▶ │ middleware: body limit,       │ ────────▶ │ Claude Code CLI (bundled) │
│ hooks + TripContext  │  X-Session-Id│  security headers, CORS,      │           │  tools: WebSearch,        │
│ services/api.js      │ ◀─────────── │  rate limit, error handlers   │ ◀──────── │  WebFetch, mcp__travel__* │
└──────────────────────┘              │ routes → controller           │  results  └──────────────────────────┘
                                      │ services: session store,      │                 │
                                      │  agent service, PDF service   │                 ▼
                                      └───────────────────────────────┘         Anthropic API
```

| Concern | Where |
|---|---|
| Presentation and interaction | `frontend/src/components`, `pages`, `layouts`, `styles` |
| Client state and logic | `frontend/src/context/TripContext.jsx`, `hooks/useChat.js`, `hooks/useItinerary.js` |
| API calls | `frontend/src/services/api.js` (the only place that calls `fetch`) |
| HTTP API and validation | `backend/src/routes`, `validators`, `middleware` |
| Orchestration | `backend/src/controllers/session_controller.py`, `services/agent_service.py` |
| Conversation state | `backend/src/services/session_store.py` (in memory) |
| Questionnaire logic | `agents/travel_planner/questionnaire.py` |
| Generation and refinement context | `agents/travel_planner/generation.py`, `refinement.py` |
| Model output validation | `agents/travel_planner/validation.py`, `schemas.py` |
| External travel data | Claude's WebSearch and WebFetch tools only (no third-party travel APIs) |
| PDF generation | `backend/src/services/pdf_service.py` (ReportLab, in memory) |

## Why Python instead of the Node backend in `requirement.md`

`requirement.md` sketches a Node backend (`app.js`, `package.json`). We use **Python and FastAPI** because:

1. The agent is built on the **Claude Agent SDK**. Its Python package bundles the Claude Code CLI and provides in-process MCP tools (`create_sdk_mcp_server`), so the agent and API run in one process without a separate tool server.
2. Pydantic gives a single schema for request validation, tool input validation and itinerary validation.
3. ReportLab produces print-quality PDFs in memory without a headless browser.

The folder split (frontend / backend / agents / personal-info / docs) follows the requirement. The backend reads the agent package from `travel_partner/agents` via the path set up in `backend/src/__init__.py`.

## A conversational turn

1. The frontend `POST /api/chat` sends `{message, skip_question?}` with the `X-Session-Id` header.
2. Middleware enforces the body size limit (16 KB), CORS and rate limits. Pydantic validates the message (at most 2,000 characters, no unknown fields).
3. The controller checks the per-session message cap and lock (one turn at a time). It then **redacts** card numbers, SSNs, passport numbers, IBANs and API-key-like strings from the message.
4. `AgentService` marks any skipped question, then calls `ClaudeTravelAgent.run_turn()` under `asyncio.wait_for` (240 s by default).
5. The agent builds a prompt containing: known preferences (JSON), the open questions computed by `questionnaire.py`, the current itinerary (when refining), the last 10 messages, and the new message. Untrusted text has `<` and `>` escaped so it cannot close the prompt's tags.
6. The model replies and calls our tools:
   - `update_preferences` merges the new details. List fields are unioned, and the model cannot touch `skipped`.
   - `ask_question` sets one question card. It is rejected if the traveler skipped that question.
   - `submit_itinerary` validates against the `Itinerary` schema and checks day numbering and that the day count matches. Rejections go back to the model with the reasons, so it can fix and resubmit.
7. The session stores the reply, preferences, question and (if any) a **new itinerary version**. The full state is returned.

## The six initial questions

All six initial questions (destination, dates, trip length, travelers, budget, interests) are asked before any destination suggestions or itinerary. Each one can be skipped. Three layers enforce this:

1. **Prompt guidance.** `generation_hint()` tells the model which core question to ask next and forbids building the itinerary until all six are settled. Once they are, it either asks for 2–3 destination suggestions based on all six answers, if the traveler wanted suggestions, or asks for the itinerary.
2. **Tool guard.** `submit_itinerary` rejects an itinerary while any core question is open, or while a suggested destination hasn't been chosen.
3. **Service guard.** `AgentService.chat()` discards a premature itinerary. If the model didn't ask a core question, it shows the next open one, so the cards always walk through all six.

A question counts as settled when its preference is known, the traveler skipped it (`skip_question`), or they replied to its card (`answering`, recorded in the app-controlled `Preferences.answered` list). The model can't set `skipped` or `answered`.

`SessionState` reports `open_core_questions`, `ready_to_generate` and `awaiting_destination_choice`. The frontend uses them, through `isItineraryTurn()` in `hooks/useItinerary.js`, to show the **flight-loading animation** (`components/FlightLoader.jsx`) while an itinerary is being built or refined.

## Itinerary versions and confirmation

- Each `submit_itinerary` appends a version (1, 2, 3, …). Versions are never edited in place.
- `POST /api/itinerary/confirm {version}` succeeds only if `version` is the latest. Confirming an outdated version returns 409.
- `GET /api/itinerary/pdf` renders **only the confirmed version**. If the traveler refines after confirming, the PDF keeps the confirmed version until they confirm again, and the UI says so.

## API contract

All responses are JSON unless noted. Errors are always `{"error": {"code": str, "message": str}}`.

| Method and path | Body | Success | Errors |
|---|---|---|---|
| `GET /api/health` | none | `{status, agent_configured}` | none |
| `POST /api/sessions` | none | 201 `SessionState` with `session_id`, greeting and first question | 429, 503 `busy` |
| `GET /api/session` | none (header) | `SessionState` | 404, 422 |
| `DELETE /api/session` | none (header) | 204 | 422 |
| `POST /api/chat` | `{message: 1–2000 chars, skip_question?: key, answering?: key}` | `SessionState` | 404, 409 `busy`, 413, 422, 429, 502, 503 `agent_not_configured`, 504 |
| `POST /api/itinerary/confirm` | `{version: int}` | `SessionState` (stage `confirmed`) | 404, 409 `no_itinerary` or `stale_version`, 422 |
| `GET /api/itinerary/pdf` | none (header) | `application/pdf`, fixed filename `travel-itinerary.pdf` | 404, 409 `not_confirmed`, 429 |

`SessionState` has the fields `reply`, `notice` (for example the privacy redaction notice), `question {key, text, options[], multi_select, optional}`, `preferences`, `stage` (`gathering`, `drafting` or `confirmed`), `itinerary {itinerary, version, confirmed_version}` `messages_remaining`, `open_core_questions`, `ready_to_generate` and `awaiting_destination_choice`.

The itinerary schema is in `agents/travel_planner/schemas.py`. It contains days, activities, travel legs (duration and distance), lodging, restaurants, a budget with assumptions, booking links (http/https only), travel notes and caveats.

## Data retention

| Data | Where | How long |
|---|---|---|
| Trip preferences, messages, itinerary versions | Backend process memory | Until 60 minutes of inactivity (`SESSION_TTL_MINUTES`), `DELETE /api/session`, or a server restart |
| Session token | Browser memory (React state) only | Until the tab is refreshed or closed |
| Conversation text | Never written to disk. The SDK runs with `--no-session-persistence`, and the server logs record only method, path and status | none |
| Anthropic API | Prompts are sent to Anthropic to generate replies | See Anthropic's data retention policy |

No accounts, cookies, analytics or browser storage are used.

## Agent sandboxing

`ClaudeTravelAgent._options()` configures the agent as follows:

- `tools=["WebSearch","WebFetch"]` sets the base toolset. `allowed_tools` adds our three MCP tools, and `disallowed_tools` blocks Bash, the file tools, Task, Agent and the rest.
- `permission_mode="dontAsk"` denies anything that isn't pre-approved.
- `setting_sources=[]`, a private temp `CLAUDE_CONFIG_DIR` and an empty temp `cwd` mean no user or project settings, memories, CLAUDE.md files or stored logins are loaded.
- `strict_mcp_config=True` means only our in-process MCP server is loaded.
- `max_turns` and `max_budget_usd` cap each turn.

This was checked against the bundled CLI (v0.2.174 SDK). Its init message lists exactly `WebFetch, WebSearch, mcp__travel__ask_question, mcp__travel__submit_itinerary, mcp__travel__update_preferences`.
