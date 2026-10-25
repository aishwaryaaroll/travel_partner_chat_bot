# Setup (Windows, PowerShell)

For installing the prerequisites (Python 3.10+, Node.js 22+ LTS, Git), see `../../README.md`. Node 24 LTS also works.

## 1. API key

Edit `travel_partner/personal-info/.env` (it already exists and is gitignored):

```
ANTHROPIC_API_KEY=sk-ant-...
MODEL=claude-sonnet-5-5
ALLOWED_ORIGINS=http://localhost:5173
SESSION_TTL_MINUTES=60
```

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | yes (for chat) | none | Used only by the backend's agent. Without it, `/api/chat` returns 503. |
| `MODEL` | no | `claude-sonnet-5-5` | Model for the travel agent |
| `ALLOWED_ORIGINS` | no | `http://localhost:5173` | Comma-separated CORS allow-list (`*` is ignored) |
| `SESSION_TTL_MINUTES` | no | `60` | Idle time before a trip is discarded |
| `AGENT_TIMEOUT_SECONDS` | no | `240` | Maximum time for one agent turn |
| `AGENT_MAX_BUDGET_USD` | no | `1.0` | Maximum spend per agent turn |
| `MAX_MESSAGES_PER_SESSION` | no | `60` | Total messages (yours and the agent's) per trip |
| `RATE_LIMIT_CHAT` | no | `20/minute` | Per-IP chat limit |

Frontend (optional): copy `frontend/.env.example` to `frontend/.env` to change `VITE_API_BASE_URL` (default `http://localhost:8000`). **Never put secrets in `VITE_*` variables.** They are bundled into the browser.

## 2. Backend

```powershell
cd travel_partner\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn src.app:app --reload --reload-dir src --reload-dir ../agents --port 8000
```

Check it at http://localhost:8000/api/health. It should return `{"status":"ok","agent_configured":true}`.

## 3. Frontend (second terminal)

```powershell
cd travel_partner\frontend
npm install
npm run dev
```

Open http://localhost:5173.

> If `node` isn't found right after installing Node, open a new terminal so it picks up the PATH change. If npm says *"running scripts is disabled"*, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## 4. Tests and checks

```powershell
# backend (from travel_partner\backend, venv active)
pytest                 # 62 offline tests (the agent is faked)
pytest -m live         # 2 optional tests against the real API; needs the key and costs a few cents
ruff check . ..\agents
bandit -r src ..\agents
pip-audit -r requirements.txt

# frontend (from travel_partner\frontend)
npm test
npm run lint
npm run build
npm audit
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Chat says "travel agent isn't configured" | Add `ANTHROPIC_API_KEY` to `personal-info/.env` and restart uvicorn |
| "Can't reach the travel planner" | Start the backend on port 8000, or set `VITE_API_BASE_URL` |
| CORS error in the browser console | Add the frontend's exact origin to `ALLOWED_ORIGINS` |
| "That took too long" | Itinerary generation with web research can take 1–3 minutes. Retry, or raise `AGENT_TIMEOUT_SECONDS` |
| "The AI service account has no credits left" | Add credits at https://console.anthropic.com/ (Settings → Billing). The key itself is fine |
| "The AI service rejected the API key" | Check the key in `personal-info/.env`: no spaces or quotes around it. Create a new key if needed |
| 502 "travel agent is unavailable" | Usually a network problem. The server log shows the error type and HTTP status only |
