# agents/travel_planner

The travel agent, built on the Python **Claude Agent SDK**. The backend calls `ClaudeTravelAgent.run_turn()` once per user message.

| File | Role |
|---|---|
| `instructions.md` | System prompt: questioning rules, itinerary rules, honesty, privacy and security rules |
| `agent.py` | Builds the per-turn prompt and the locked-down `ClaudeAgentOptions`, runs `query()`, and returns a `TurnResult` |
| `tools.py` | In-process MCP tools: `update_preferences`, `ask_question`, `submit_itinerary`. They only write to a `TurnState` |
| `questionnaire.py` | The 6 core questions, the rules for which follow-ups are relevant, skip handling and preference merging. Decides deterministically what is still open, so answered or skipped questions aren't asked again |
| `generation.py` | Builds the `<state>` block (preferences, open questions, recent history, guidance) and escapes untrusted text |
| `refinement.py` | Itinerary context for refinement turns, plus the quick-change messages |
| `validation.py` | Itinerary schema and consistency checks, and redaction of sensitive data |
| `schemas.py` | Pydantic models: `Preferences`, `Itinerary`, `Question`, … |

Each turn is **stateless**: the backend passes the state in, and the SDK keeps nothing on disk (`--no-session-persistence`). The model can use only WebSearch, WebFetch and the three tools above. See `../docs/architecture.md` for the sandbox settings.

The API key comes from `personal-info/.env` through the backend's settings. It's passed to the CLI subprocess as an environment variable and never placed in a prompt.
