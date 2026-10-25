# Travel Partner ✈

An AI travel-planning chatbot with a scrapbook-style UI. Chat with it, answer a few quick questions (or skip them), and get a day-by-day itinerary. Refine it ("less driving", "more relaxed"), confirm it, and download it as a PDF.

```
travel_partner/
├── frontend/       React + Vite (scrapbook UI)
├── backend/        FastAPI API, validation, sessions, PDF
├── agents/         travel_planner agent (Claude Agent SDK)
├── personal-info/  LOCAL ONLY: .env with your ANTHROPIC_API_KEY (gitignored)
└── docs/           architecture.md · security.md · setup.md
```

## Quick start

1. Put your key in `personal-info/.env`: `ANTHROPIC_API_KEY=sk-ant-...`
2. Start the backend:
   ```powershell
   cd backend; python -m venv .venv; .venv\Scripts\activate
   pip install -r requirements.txt -r requirements-dev.txt
   uvicorn src.app:app --reload --reload-dir src --reload-dir ../agents --port 8000
   ```
3. Start the frontend:
   ```powershell
   cd frontend; npm install; npm run dev
   ```
4. Open http://localhost:5173

For full details see [docs/setup.md](docs/setup.md). For how it works see [docs/architecture.md](docs/architecture.md). For the security audit see [docs/security.md](docs/security.md).

## Known limitations

- Sessions are in memory. Restarting the backend or refreshing the page starts a new trip.
- Prices, hours and conditions are AI estimates informed by web search. They are labelled as estimates, and nothing is booked.
- Generating an itinerary with web research can take 1–3 minutes, and responses are not streamed.
- The app is designed for local or single-process use. See `docs/security.md` (F-3, F-4, F-9) before deploying publicly.
