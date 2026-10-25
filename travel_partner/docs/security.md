# Security review

**Date:** 2026-10-25 · **Scope:** `travel_partner/` (frontend, backend, agents, config) · **Reviewer:** Claude Code (automated tools plus manual code review)

> This review reduces risk but does **not** show the application is free of vulnerabilities. Results from automated scanners are listed separately from the manual review. Limitations are listed at the end.

## 1. Automated checks

| Tool | Command | Result |
|---|---|---|
| pytest (backend, includes 20+ security tests) | `pytest` | **62 passed** (2 live tests deselected) |
| Vitest (frontend, includes XSS and URL tests) | `npm test` | **31 passed** |
| Ruff (with the `S` bandit rules, `B`, `BLE`) | `ruff check . ../agents` | **All checks passed** |
| Bandit | `bandit -r src ../agents` | 1 Low finding (B406), judged a false positive; see F-2 |
| pip-audit | `pip-audit -r requirements.txt` | **No known vulnerabilities** |
| npm audit | `npm audit` | Initially 3 (2 critical, 1 moderate); **0 after the fix**; see F-1 |
| ESLint (`react/no-danger`, `jsx-no-target-blank`, innerHTML ban, no-eval) | `npm run lint` | **Clean** |
| Bundle secret scan | `grep -rE "sk-ant\|ANTHROPIC" dist/` | **No matches** |
| Repo secret scan | `test_no_secrets_in_tracked_config_files` (regex over every project file except `personal-info/`, `node_modules/`, `.venv/`) | **No matches** |
| Agent toolset (live CLI init, fake key) | `query()` with the production options | Tools exactly `WebFetch, WebSearch, mcp__travel__*`; permission mode `dontAsk` |
| Running server smoke test | uvicorn + curl | Headers present; errors are generic JSON; access log has only method, path and status |

## 2. Manual review by area

### A. Secrets and configuration
- The real key lives only in `personal-info/.env`. `.gitignore` covers `.env`, `.env.*` (except `.env.example`) and `personal-info/*` (except `README.md` and `.gitkeep`). A test enforces these rules.
- The key is held as a Pydantic `SecretStr`, so it is masked in reprs and dumps (tested). It reaches the agent subprocess only as the `ANTHROPIC_API_KEY` environment variable, never in prompt text (tested).
- The frontend's only environment variable is `VITE_API_BASE_URL` (tested). The built bundle contains no key material.
- Logging: only the error type, never the message, prompt or reply content (tested by static check). Uvicorn access logs show paths, and the session token is in a header, never in the URL.

### B. Frontend
- All model and user content renders as React text. `RichText` splits lines into `<p>`/`<li>` without parsing HTML. There is no `dangerouslySetInnerHTML` or `innerHTML` (enforced by lint). Tests confirm that `<img onerror>` and `<script>` payloads render as text.
- Every external link goes through `safeUrl()`, which allows absolute http/https only and rejects credentials in URLs, `javascript:`, `data:`, `file:` and protocol-relative URLs. Links render with `target="_blank" rel="noopener noreferrer"` (tested).
- Production builds include a strict CSP meta tag (`script-src 'self'`, `object-src 'none'`, `connect-src` limited to the API). The `fetch` calls use `credentials: 'omit'` and `referrerPolicy: 'no-referrer'`.
- No browser storage is used, so the session token is lost on refresh by design.

### C. Backend
- **Validation:** strict Pydantic models with `extra="forbid"` and length and size caps on every request field and every model-produced field. Malformed JSON, wrong types, extra fields and over-long messages return 422 without echoing the submitted values (tested).
- **Size and abuse limits:** a 16 KB body cap that enforces streamed bodies too, not just Content-Length (tested 413). Also a 2,000-character message cap, a per-session message cap (tested 429), one agent turn at a time per session (tested 409), a 240 s agent timeout (tested 504), a per-turn `max_turns`/`max_budget_usd` cap, and a maximum number of concurrent sessions.
- **Rate limits** (slowapi, per IP): 10/min for session creation (tested), 20/min for chat, 10/min for PDF, 60/min default.
- **CORS:** an explicit allow-list with `*` ignored (tested), no credentials, and only `Content-Type`/`X-Session-Id` headers allowed.
- **Headers:** `nosniff`, `X-Frame-Options: DENY`, `CSP default-src 'none'; frame-ancestors 'none'`, `Referrer-Policy: no-referrer`, COOP/CORP, `Permissions-Policy`, `Cache-Control: no-store`, and the `Server` header removed (tested).
- **Errors:** every exception maps to `{error:{code,message}}`. Unhandled errors return a generic 500, with no traces, paths or exception text (tested). The OpenAPI and docs endpoints are disabled.
- **Access control:** no accounts. Each session is reachable only with its random 256-bit token (`secrets.token_urlsafe(32)`), which is validated by a pattern.
- **Injection:** there is no SQL, shell or template engine, and no `eval`. The PDF filename is fixed, and no file paths come from input. The PDF is built in memory, and all text is XML-escaped before ReportLab's mini-markup parser sees it. A test confirms markup becomes literal text, with no `/URI` link annotations and no images.

### D. AI-specific
- **Tool lockdown:** only WebSearch, WebFetch and three in-process tools that just write to a per-turn object. There is no Bash, file access, Task or subagents. `cwd` is an empty temp dir, the config dir is private, no settings or memories are loaded, and no transcripts are persisted. Verified against the real CLI.
- **Prompt injection:** the system prompt says user and web content are untrusted. User text and history have `<`/`>` escaped so they can't break out of `<traveler_message>` (tested). Even if the model is manipulated, it has no secrets in context and no tools that can reach the environment or file system. Its only outputs are schema-validated data and text that renders as plain text.
- **Output validation:** every tool input is validated by Pydantic. Itineraries must pass the schema, sequential day numbering and the day-count check before they are stored. Links must be http/https.
- **Privacy:** the prompt forbids asking for DOB, passport numbers, SSNs, card or bank details, passwords and IDs, and allows passport nationality only when needed. Incoming messages and all strings in tool arguments are redacted for card numbers (Luhn-checked), SSNs, passport numbers, IBANs and `sk-ant-` keys before they are stored or sent (tested), and the user is told.
- **Honesty:** the prompt requires costs to be labelled as estimates, unverifiable items to go in caveats, and no booking claims. The UI and PDF always add a "nothing is booked; verify prices and hours" caveat.

## 3. Findings

| ID | Severity | Finding | Evidence / files | Status |
|---|---|---|---|---|
| F-1 | **Critical (dev-only)** | `vitest@3` pulled in `tinypool` (prototype pollution → RCE, GHSA-5gmw-xhrv-c9v3, GHSA-85c8-ppgw-ccpr) and `@vitest/mocker` (path traversal, GHSA-82fw-gwwq-j7x9) | `npm audit`; `frontend/package.json` | **Fixed:** upgraded to `vitest@^5.0.5`; `npm audit` reports 0. These were test-tooling packages, not in the shipped bundle |
| F-2 | Low (false positive) | Bandit B406: `xml.sax` import | `backend/src/services/pdf_service.py:10` | Only `saxutils.escape` is used and no XML is parsed. Annotated `# nosec B406` with the reason |
| F-3 | Medium | Rate limits and sessions are in memory and per process. Behind a reverse proxy, `get_remote_address` sees the proxy IP, so all users would share one limit. Multiple workers would each have separate limits and sessions | `middleware/rate_limit.py`, `services/session_store.py` | **Open.** Fine for local single-process use. For deployment, use one worker or Redis-backed storage, and trust `X-Forwarded-For` only from the known proxy |
| F-4 | Medium | The session token is a bearer credential, and local dev uses plain HTTP | `routes/sessions.py` | **Open.** Serve over HTTPS in any shared deployment. Tokens expire after 60 minutes idle |
| F-5 | Medium | Prompt injection through web pages the model fetches cannot be fully prevented. A manipulated model could produce misleading text or a phishing-style (but http/https) link in an itinerary | `agents/travel_planner/*` | **Mitigated, not eliminated.** Tool lockdown, schema validation, text-only rendering and no secrets in context. Users should verify links before booking |
| F-6 | Low | The agent CLI subprocess inherits the backend's environment variables (an SDK behaviour). The model has no tool that can read them, but any other secrets in that environment are present in the subprocess | `agents/travel_planner/agent.py` | **Open.** Run the backend with a minimal environment that holds only this app's settings |
| F-7 | Low | PII redaction is pattern-based and may miss unusual formats (for example, IDs written in words) | `agents/travel_planner/validation.py` | **Accepted.** The prompt also tells the model never to ask for or repeat such data |
| F-8 | Low | The CSP is a `<meta>` tag in production builds only. The dev server has none, and `style-src 'unsafe-inline'` is needed for React style attributes (CSS custom properties) | `frontend/vite.config.js` | **Open.** Set the CSP as an HTTP header at the hosting layer in production |
| F-9 | Low | Cost abuse: at most about 30 agent turns per session × $1 per-turn budget cap; sessions are free to create (10/min/IP) | `config.py` | **Open.** Lower `AGENT_MAX_BUDGET_USD` and add a global spend limit or auth for public deployment |
| F-10 | Info | npm blocked esbuild's postinstall script (new npm default). The build works using esbuild's platform package | `npm install` output | No action needed |

## 4. Checks not performed

| Check | Why not | Recommendation |
|---|---|---|
| Git history secret scan | No git repository exists yet (the user will initialise and push later) | Before the first push, run `git status` and `git ls-files` to confirm `personal-info/.env` is untracked. Run `gitleaks detect` or `git log -p | grep sk-ant` after commits exist. If a key is ever committed, **revoke it in the Anthropic console**; deleting the file is not enough |
| Live prompt-injection and extraction tests against the real model | The API key was not configured at review time | Run `pytest -m live` once the key is added. Also try manual adversarial prompts |
| Dynamic scanning (DAST, for example OWASP ZAP) | Out of scope for a local review. No production deployment exists | Run against a staging deployment |
| Load testing of rate limits under concurrency | Only functional tests were run | Load-test before any public deployment |
| Authentication and authorization review | No accounts or persistent user data exist by design | Revisit if accounts are added |

## 5. Re-audit (2026-10-25, after the Windows subprocess fix)

**Code changed since the first review:** `agents/travel_planner/agent.py`. Agent turns now run in a worker thread on Windows selector loops, and API account errors map to fixed messages.

| Check | Result |
|---|---|
| pytest | 66 passed (4 new error-mapping tests) |
| Vitest / ESLint / build | 31 passed / clean / ok |
| ruff, bandit | clean, 0 issues |
| pip-audit (whole installed venv) | No known vulnerabilities |
| npm audit | 0 vulnerabilities |
| Bundle secret scan; `innerHTML` / `eval` / browser-storage grep in `src/` | none |

**Manual review of the changes:**
- The account-error mapper only substring-matches the SDK error text. It returns one of four fixed strings and never echoes the error detail (tested).
- The worker-thread path keeps an inner `asyncio.wait_for` with the configured timeout, so the thread finishes even if the HTTP request is abandoned. The outer timeout in `AgentService` still applies.

**New finding:**

| ID | Severity | Finding | Status |
|---|---|---|---|
| F-11 | Low | On Windows, if a client disconnects mid-turn, the agent thread keeps running (and spending) until the turn ends or hits its timeout, bounded by `AGENT_TIMEOUT_SECONDS`, `agent_max_turns` and `AGENT_MAX_BUDGET_USD` | Accepted for local use |

**Network exposure (local machine):**

| Port | Bound to | Process | Assessment |
|---|---|---|---|
| 8000 | `127.0.0.1` | uvicorn (backend) | Loopback only; not reachable from the network |
| 5173 | `::1` | Vite dev server | Loopback only; not reachable from the network |
| 135, 139, 445, 5040, 7680, 49664–49669 | all interfaces | Windows services (RPC, SMB, delivery optimisation) | Standard Windows. The Wi-Fi network is set to **Public**, the firewall is on for all profiles, and there are no inbound File and Printer Sharing allow rules, so inbound traffic is blocked by default |
| 29250, 64909, 42050 | loopback | VS Code, OneDrive | Local only |

Do not start the servers with `--host 0.0.0.0` (uvicorn) or `--host` (Vite) unless you mean to expose them on your network.

## 6. Re-audit (2026-10-25, all-six-questions and flight animation)

**Changes reviewed:**
- the new `answering` request field
- the app-controlled `Preferences.answered` list
- the `submit_itinerary` guard
- the next-question fallback and itinerary discard in `AgentService`
- the three new `SessionState` fields
- `FlightLoader.jsx` and its CSS

| Check | Result |
|---|---|
| pytest | 88 passed (22 new, in `test_all_six_questions.py`) |
| Vitest / ESLint / build | 45 passed (14 new, in `flight.test.jsx`) / clean / ok |
| ruff, bandit, pip-audit, npm audit | clean, 0 issues, no known vulnerabilities, 0 vulnerabilities |
| Bundle secret scan, unsafe-HTML grep | none |

**Manual review notes:**
- `answering` uses the same strict `^[a-z_]{1,40}$` pattern as `skip_question` (tested with traversal and injection strings). Unknown keys are ignored by `mark_answered`.
- The model cannot set `answered` or `skipped`. They are removed from the tool schema and ignored by `merge_preferences` (tested), so a prompt-injected model cannot mark questions settled to skip ahead.
- The animation renders the destination name as React text (tested with an HTML payload), uses no external assets, and respects `prefers-reduced-motion`.

**New findings:** none. All earlier open items (F-3 to F-9, F-11) are unchanged.
