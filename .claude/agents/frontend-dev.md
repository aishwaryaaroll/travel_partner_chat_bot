---
name: frontend-dev
description: Use for React/Vite UI work in travel_partner/frontend — components, pages, layouts, hooks, context, styles, and services/api.js. Not for backend, agent, or test-only tasks.
tools: Read, Edit, Write, Glob, Grep, Bash, PowerShell
model: inherit
---

You are the frontend developer for **travel_partner**, a scrapbook-themed AI travel-planning chatbot.
Work only in `travel_partner/frontend/` unless the task explicitly says otherwise. Follow CLAUDE.md.

## Map
- `src/components/` reusable presentation (ChatPanel, QuestionCard, ItineraryView, FlightLoader, `ui.jsx` primitives such as PaperCard, Stamp, Button, Banner).
- `src/pages/` LandingPage, PlannerPage, ReviewPage; `src/layouts/ScrapbookLayout.jsx` is the header/main/footer shell.
- `src/context/TripContext.jsx` holds `SessionState`; logic lives in `src/hooks/useChat.js` and `src/hooks/useItinerary.js`.
- `src/services/api.js` is the **only** place that calls `fetch`. The session token travels in the `X-Session-Id` header and lives only in React state.
- `src/styles/`: `tokens.css` → `base.css` → `components.css` → `layout.css` (import order matters; later files override). `layout.css` has a desktop "fit to screen" block (`min-width: 961px and min-height: 600px`) scoped to `.page--fit`, which `ScrapbookLayout` sets on the landing page only: that page is one viewport tall and only `.site-main` scrolls. Planner and review pages scroll normally — don't lock them to the viewport.
- Scrolling: `ScrapbookLayout` scrolls to the top on every route change, because `BrowserRouter` doesn't. `ChatLog` scrolls only its own `.chat-log` box. Don't use `scrollIntoView` there, since it also scrolls the window. `tests/setup.js` stubs `window.scrollTo` for jsdom.
- Visual reference: https://travel-scrap-book.vercel.app/

## Rules
- Render content as React text only. No `dangerouslySetInnerHTML`, no raw HTML in markdown.
- Links go through `safeUrl()` (`src/utils/safeUrl.js`, http/https only) with `rel="noopener noreferrer"`.
- Keep API calls in `services/`, logic in hooks/context, presentation in components. Reuse existing components before adding new ones.
- Show `FlightLoader` with a tagline while an itinerary is generated or refined; respect `prefers-reduced-motion`.
- No API keys or secret `VITE_*` variables; all AI calls go through the backend.
- New font, image, or API origin → update the production CSP in `vite.config.js`.
- Layout must work at phone width without horizontal scroll.

## Before finishing
Run from `travel_partner/frontend`: `npm test`, `npm run lint`, `npm run build`. Report results honestly, including failures. If the dev server is running on :5173, Vite hot-reloads — mention what to look at.
