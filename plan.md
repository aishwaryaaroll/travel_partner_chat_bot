# travel_partner: implementation plan

## Context
`chat_bot/` holds only `requirement.md`, `CLAUDE.md` and `README.md` (the prerequisites guide). No code exists yet and it is not a git repo. The goal is to build the AI travel-planning chatbot described in `requirement.md`: a scrapbook-themed React UI, a conversational questionnaire, day-by-day itinerary generation and refinement, a confirm step, PDF export, tests, a security audit and setup docs. Stack decisions are already fixed in `CLAUDE.md`: FastAPI with the Python `claude-agent-sdk`, React with Vite, root at `chat_bot/travel_partner/`, WebSearch/WebFetch only, in-memory sessions.

## Prerequisite check (run 2026-10-25)
| Item | Status |
|---|---|
| Python 3.10+ | ✅ 3.14.7 (only version installed; fall back to 3.13 if a wheel is missing) |
| pip | ✅ 26.2.1 |
| Git | ✅ 2.56.0, but ⚠️ **`user.name` and `user.email` are not set** (needed before the first commit) |
| Node.js + npm | ✅ Node v24.22.1 and npm 11.19.1 in `C:\Program Files\nodejs`, which is on the machine PATH. The current shell started before the install, so **open a new terminal** or restart Claude Code to pick up PATH. Node 24 is an LTS line, so it is fine instead of 22. |
| PowerShell execution policy | ✅ RemoteSigned (npm scripts will run) |
| winget | ✅ available |
| Anthropic API key | ⏳ The user adds it to `travel_partner/personal-info/.env` once Phase 1 creates that file |

## Phase 1: scaffold and secret hygiene
- `git init` in `chat_bot/`, with a `.gitignore` covering `.env`, `.env.*`, `!.env.example`, `personal-info/*`, `!personal-info/README.md`, `!personal-info/.gitkeep`, `node_modules/`, `.venv/`, `dist/`, `__pycache__/`.
- Create the folder tree from `CLAUDE.md` (`frontend/`, `backend/src/{routes,controllers,middleware,services,validators,utils}`, `backend/tests/`, `agents/travel_planner/`, `personal-info/`, `docs/`).
- **Create `personal-info/.env`** with `ANTHROPIC_API_KEY=` left blank, plus `ALLOWED_ORIGINS=http://localhost:5173`, `SESSION_TTL_MINUTES=60` and `MODEL=claude-sonnet-5-5`. **Pause here so the user can paste the key.**
- Add placeholder `backend/.env.example` and `frontend/.env.example` (frontend holds only `VITE_API_BASE_URL`), plus `personal-info/README.md`.
- The backend loads env from `../personal-info/.env` with `pydantic-settings`.

## Phase 2: backend (FastAPI)
- `src/app.py` sets up the app factory, CORS from `ALLOWED_ORIGINS`, security-headers middleware, a body-size limit, `slowapi` rate limiting, and a generic error handler that returns no stack traces.
- `src/services/session_store.py` keeps in-memory sessions keyed by a random UUID, with an idle TTL and a turn cap. Each session holds the preferences, messages, itinerary versions and the confirmed version id.
- Validators are Pydantic models: `ChatRequest` (message ≤ 2,000 chars), `Preferences`, and `Itinerary` (title, destination, dates, days[], activities, travel times and distances, lodging, restaurants, budget with assumptions, links, caveats).
- API contract:
  - `POST /api/sessions` returns `{session_id}`.
  - `POST /api/sessions/{id}/messages` returns `{reply, question?, options?, preferences, itinerary?}`. Streaming over SSE is optional.
  - `GET /api/sessions/{id}/itinerary` returns the latest version.
  - `POST /api/sessions/{id}/itinerary/confirm` takes `{version}`.
  - `GET /api/sessions/{id}/itinerary/pdf` returns 409 unless an itinerary is confirmed.
  - `GET /api/health`.
- `src/services/pdf_service.py` uses ReportLab to build the PDF in memory with `BytesIO`, from the confirmed version only, with all text escaped and a fixed filename.
- Tooling: `requirements.txt` and `requirements-dev.txt` (pytest, httpx, ruff, bandit, pip-audit).

## Phase 3: agent (`agents/travel_planner/`)
- `instructions.md` is the system prompt: the six initial questions, dynamic follow-ups, a no-re-asking rule, the privacy deny-list, an anti-prompt-injection rule, "label estimates and never claim a booking", and "call `submit_itinerary` with structured JSON".
- `tools.py` holds in-process SDK MCP tools (`update_preferences`, `ask_question`, `submit_itinerary`). Each validates its input with Pydantic and writes to the session.
- `agent.py` builds `ClaudeAgentOptions` with `allowed_tools=[WebSearch, WebFetch, mcp__travel__*]`, `disallowed_tools=[Bash, Read, Write, Edit, Glob, Grep, Task, ...]`, `cwd` set to an empty temp dir, a max-turns cap and an `asyncio.wait_for` timeout. The API key comes from the environment and never enters prompt text.
- `questionnaire.py` decides deterministically which questions are still missing, using the preference state, and supplies the multi-select interest options.
- `generation.py` and `refinement.py` hold the prompt builders, and refinement passes the current itinerary plus the change request.
- `validation.py` holds the schema check plus a privacy filter that rejects or redacts prohibited data patterns.
- `README.md` documents all of the above.

## Phase 4: frontend (React + Vite)
- First, inspect https://travel-scrap-book.vercel.app/ for its palette, fonts, paper textures, tape and polaroid elements, and card layering.
- Pages: `Landing`, `Planner` (chat and questionnaire, plus a live itinerary panel), `Review` (confirm and download PDF).
- Components: `ScrapCard`, `Polaroid`, `TapeLabel`, `Button`, `ChipSelect` (multi-select interests), `ChatBubble`, `ChatInput`, `QuestionCard` with a skip action, `DayCard`, `ItineraryView`, `RefineBar` (quick chips like less driving, more nature, lower budget, more relaxed), `ConfirmPanel`.
- `services/api.js` wraps fetch. `context/TripContext.jsx` and `hooks/useChat.js` / `useItinerary.js` hold the logic. `utils/safeUrl.js` allows http/https only.
- Styles: CSS variables and responsive breakpoints. All content renders as React text, with no `dangerouslySetInnerHTML`.
- Tests use Vitest and React Testing Library. Lint with ESLint.

## Phase 5: tests
- Backend (pytest) mocks the agent client: the questionnaire flow and missing questions, parsing several answers from one message (preference extraction via the tool), invalid and missing input, generation and refinement producing a new version, the confirm flow, a PDF that contains the confirmed version rather than a later draft, 409 before confirmation, validation errors, oversized bodies, rate limits, CORS, security headers, no stack traces, config not leaking the key, the privacy filter, and prompt-injection strings that cannot alter tool config.
- Frontend: `safeUrl`, the multi-select chips, chat rendering escaping HTML, and the confirm/download button state.
- One optional live smoke test runs only when `ANTHROPIC_API_KEY` is set.

## Phase 6: security audit and docs
- Run `pytest`, `ruff`, `bandit -r src ../agents`, `pip-audit`, `npm audit`, `npm run lint`, `npm run build`, then grep `dist/` for `sk-ant` and run `git ls-files` plus a history scan for secrets.
- `docs/security.md` covers the checks, tools, findings by severity, evidence, remediation, remaining risks and checks not performed. It separates automated results from manual review and makes no "vulnerability-free" claim.
- `docs/architecture.md` explains why Python replaces Node, the data flow, what is retained in memory, and the API contract. `docs/setup.md` gives the setup steps.

## Verification
1. `uvicorn src.app:app --reload --port 8000` and `npm run dev` start, and `GET /api/health` returns OK.
2. End to end in the browser: answer the questions (including skipping one), get an itinerary, refine it ("more relaxed"), confirm, download the PDF, and check that it matches the confirmed version.
3. All of the test, lint, build and audit commands from Phase 6 pass, or their failures are documented.

## Before implementation, the user should
- Set git identity: `git config --global user.name "…"` and `git config --global user.email "…"`.
- Restart the terminal or Claude Code so `node` and `npm` are on PATH.
- Paste the API key into `travel_partner/personal-info/.env` when prompted after Phase 1.
