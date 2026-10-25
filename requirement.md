# Project Requirements: AI Travel Planning Chatbot

## 1. Project Objective

Build a full-stack AI-powered travel planning chatbot that interacts with users conversationally, gathers essential trip preferences, generates personalized travel itineraries, and allows users to refine and confirm their itinerary.

The application should feel like a personal travel agent, with an engaging scrapbook-inspired interface.

Before implementing anything, inspect the existing repository, understand its structure, and prepare an implementation plan. Preserve existing work wherever possible.

## 2. Frontend Requirements

**Technology:** React.js.

Use the following website as the primary visual design reference:

https://travel-scrap-book.vercel.app/

Recreate the overall visual theme as closely as reasonably possible without needing to duplicate every detail.

### Design direction
- Scrapbook-inspired travel journal aesthetic.
- Warm, inviting colors and a travel-inspired visual identity.
- Paper-like surfaces, layered cards, photo collages, and subtle decorative elements where appropriate.
- Attractive typography, generous spacing, and polished visual hierarchy.
- Smooth, restrained transitions and interactive elements.
- Responsive design for desktop, tablet, and mobile.
- Consistent buttons, form controls, cards, navigation, and typography.

Inspect the reference website before selecting the final design implementation. Reuse its visual patterns as inspiration rather than inventing an unrelated interface.

### Main screens and components
1. **Landing page:** Introduce the AI travel planner and provide a clear call to start planning.
2. **Travel questionnaire:** Collect initial trip preferences through a conversational interface.
3. **Chat interface:** Allow users to answer follow-up questions, request changes, and interact naturally with the travel agent.
4. **Itinerary view:** Display a day-by-day itinerary with destinations, activities, estimated travel times, accommodation suggestions, and estimated costs when available.
   - While an itinerary is being generated or refined, show a small animation in the itinerary area (for example a small plane flying, with a short tagline) so users know the itinerary is being built.
5. **Itinerary refinement:** Let users request changes such as less driving, more nature, a lower budget, or a more relaxed schedule.
6. **Confirmation and export:** Allow users to review and confirm the final itinerary, then download it as a PDF.

Keep the UI modular, with reusable React components and clear separation between presentation and business logic.

## 3. Initial Travel Questionnaire

Ask only essential questions at the beginning. Do not overwhelm users with a long form.

Initial questions:
1. Where would you like to go, or would you like destination suggestions?
2. When do you want to travel?
3. How long is the trip?
4. Who is traveling?
5. What is your approximate budget?
6. What experiences do you enjoy most?

For interests, support multiple selections, including mountains, lakes, waterfalls, beaches, scenic drives, hiking, cities, food, culture, relaxation, and photography.

Ask all six initial questions before generating destination suggestions or an itinerary. Users may skip any question, but each one must be asked. Base destination suggestions and the itinerary on all six answers.

### Dynamic follow-up questions
Ask additional questions only when the answers materially affect itinerary quality.

Examples:
- Departure location when transportation or routing requires it.
- Driving preferences for road trips.
- Activity level for outdoor destinations.
- Accommodation preferences when lodging recommendations are needed.
- Dietary requirements when restaurant recommendations are requested.
- Must-see attractions or activities to avoid.

Accept free-text responses as well as selectable options.

The agent must recognize information already supplied in conversation and never ask the same question again unnecessarily. Allow users to skip optional questions and proceed with sensible assumptions.

## 4. Privacy Requirements

**Never request confidential personal information that is unnecessary for travel planning.**

Do not request or store:
- Date of birth.
- Passport numbers or passport scans.
- Social Security numbers.
- Credit card or bank account details.
- Account passwords.
- Other government identification numbers.
- Unnecessary sensitive personal information.

Ask only for travel information needed to plan the itinerary.

For international travel, if entry requirements need to be researched, ask only for the relevant passport nationality or other minimum information necessary. Do not request passport numbers.

Do not send API keys, secrets, or private environment variables to the frontend or to the AI model unless strictly necessary and appropriately protected.

Avoid logging sensitive user conversations, credentials, tokens, or other secrets. Keep user data collection minimal and document what is retained.

## 5. Project Folder Structure

Organize the repository into clearly separated frontend, backend, agent, and private configuration areas.

Use the following structure as a starting point. Adapt it to the existing repository and chosen framework where necessary.

```text
travel-planner/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── context/
│   │   ├── utils/
│   │   ├── styles/
│   │   └── App.jsx
│   ├── .env.example
│   └── package.json
│
├── backend/
│   ├── src/
│   │   ├── routes/
│   │   ├── controllers/
│   │   ├── middleware/
│   │   ├── services/
│   │   ├── validators/
│   │   ├── utils/
│   │   └── app.js
│   ├── tests/
│   ├── .env.example
│   └── package.json
│
├── agents/
│   ├── travel_planner/
│   │   ├── agent instructions and configuration
│   │   ├── questionnaire logic
│   │   ├── itinerary generation
│   │   ├── itinerary refinement
│   │   └── itinerary validation
│   └── README.md
│
├── personal-info/
│   ├── .gitkeep
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   ├── security.md
│   └── setup.md
│
├── .gitignore
├── README.md
└── package.json
```

Keep the `personal-info/` directory for local-only secrets and private configuration if necessary. It must never be committed to Git.

Prefer environment variables and `.env` files for API keys. Keep real secret values in ignored local files, and provide placeholder-only `.env.example` files.

If the agent framework requires its configuration in a different location, document that decision rather than duplicating credentials.

### Git requirements
- Add `.env`, `.env.*` files containing real secrets, local credentials, and the entire `personal-info/` directory to `.gitignore`.
- Allow `.env.example` files to be committed.
- Do not commit real API keys, tokens, private keys, or credentials.
- Inspect `git status` and tracked files before committing changes.
- If a secret has already been committed, explain that it must be revoked or rotated; deleting the file alone is insufficient.

## 6. Backend and AI Agent Architecture

Keep the AI integration on the backend. The React frontend must communicate with the backend through defined API endpoints rather than accessing API keys directly.

Separate responsibilities between:
- Frontend presentation and interaction.
- Backend API and validation.
- Travel agent orchestration.
- Questionnaire and conversation state.
- Itinerary generation and refinement.
- External travel data integrations.
- PDF generation.

Define clear API contracts for the frontend and backend.

Implement appropriate input validation, error handling, timeouts, and rate limiting.

Do not fabricate current prices, booking availability, opening hours, weather, or reservation confirmations. Clearly label estimates and verify time-sensitive information through suitable data sources when integrations are available.

Do not claim a reservation or booking has been completed unless the relevant booking process actually confirms it.

## 7. Itinerary Confirmation and PDF Download

Users must be able to review and modify the proposed itinerary before confirming it.

Implement the following flow:

1. Generate a preliminary itinerary.
2. Display the itinerary in an easy-to-read format.
3. Allow users to request modifications.
4. Provide a clear **Confirm Itinerary** action.
5. After confirmation, display a **Download PDF** option.
6. Generate a downloadable PDF containing the confirmed version of the itinerary.

### PDF contents
Include:
- Trip title and destination.
- Travel dates and duration.
- Day-by-day itinerary.
- Activities and relevant locations.
- Estimated travel durations and distances when available.
- Accommodation and restaurant suggestions, if included.
- Estimated budget with clear assumptions.
- Booking links and useful travel notes.
- Relevant caveats about seasonal conditions or unverified details.

The PDF must be readable, professionally formatted, and suitable for printing.

Ensure the downloaded PDF reflects the latest confirmed itinerary, not an outdated draft. Sanitize user-provided text and use safe PDF-generation techniques.

The PDF export should not require the user to provide confidential information.

## 8. Security Audit — Mandatory

Before considering the project complete, inspect the application for security vulnerabilities.

Perform both code review and automated checks where practical.

### A. Secrets and configuration
- Search tracked files and Git history for accidentally committed credentials.
- Verify `.gitignore` coverage.
- Confirm API keys are never embedded in frontend bundles or exposed through public environment variables.
- Check that errors and logs do not reveal secrets.

### B. Frontend security
- Check for cross-site scripting (XSS).
- Avoid unsafe HTML rendering and unsafe DOM manipulation.
- Validate and safely render user-generated content.
- Review external links and URL handling.
- Check dependency vulnerabilities.

### C. Backend security
- Validate all incoming request data.
- Check for injection vulnerabilities.
- Configure CORS with explicit allowed origins.
- Apply appropriate rate limiting.
- Prevent unauthorized access to endpoints.
- Avoid exposing stack traces, internal configuration, or sensitive data in errors.
- Apply appropriate security headers.
- Review file generation and file download endpoints for path traversal or unsafe file handling.

### D. AI-specific security
- Test for prompt injection and attempts to override the travel agent's instructions.
- Treat retrieved web pages, external API responses, and user-provided content as untrusted input.
- Do not allow user content or retrieved content to override system instructions or reveal secrets.
- Prevent the model from accessing environment variables or executing arbitrary commands.
- Avoid passing API keys and secrets into model prompts.
- Validate model output before rendering it or using it in backend operations.
- Apply limits to request size, conversation length, and model usage where appropriate.

### E. Dependency and configuration checks
- Run applicable dependency vulnerability scans, such as `npm audit`.
- Run available static analysis or security linters.
- Review authentication and authorization if accounts or persistent user data are implemented.
- Check for insecure defaults and unnecessary permissions.
- Test error handling and common abuse scenarios.

### F. Security report

Create `docs/security.md` with:
- Checks performed.
- Tools and commands used.
- Vulnerabilities discovered.
- Severity: Critical, High, Medium, or Low.
- Evidence and affected files.
- Remediation applied.
- Remaining risks and recommended next steps.
- Checks that could not be performed and why.

Do not claim the application is vulnerability-free. Clearly distinguish automated scan results from a manual security review, and report any limitations.

Do not run destructive tests against external systems or production services.

## 9. Testing Requirements

Create tests for:
- Initial questionnaire and dynamic follow-up behavior.
- Parsing multiple answers from a single message.
- Handling missing or invalid information.
- Itinerary generation and refinement.
- Itinerary confirmation and PDF export.
- Backend request validation and error handling.
- Secret protection and safe environment configuration.
- Relevant security controls.

Run available tests, linting, build checks, and security scans. Fix issues where practical and report any unresolved failures.

## 10. Development Workflow

Follow this sequence:

1. Inspect the existing repository and reference website.
2. Identify the existing framework, dependencies, and current implementation.
3. Propose the architecture and implementation plan.
4. Establish the folder structure and secret-management rules.
5. Implement the React frontend using the reference design direction.
6. Implement the backend API and travel agent integration.
7. Implement dynamic questioning and itinerary generation.
8. Implement itinerary confirmation and PDF export.
9. Add and run tests.
10. Conduct the security review.
11. Update documentation with setup instructions, required environment variables, architecture, and security findings.
12. Summarize completed work, setup commands, required API keys, test results, and known limitations.

Preserve existing functionality unless a change is necessary. Do not overwrite files or discard existing work without understanding their purpose.

## Definition of Done

The project is complete when:
- The React frontend follows the scrapbook-inspired reference theme.
- The repository has clearly separated frontend, backend, agent, and private configuration areas.
- Secrets are kept out of frontend code and Git.
- The chatbot asks only necessary questions and supports conversational follow-ups.
- The user can generate and refine a personalized itinerary.
- The user can confirm the itinerary and download the confirmed version as a PDF.
- Core functionality is tested.
- A security review has been performed and documented.
- Setup instructions enable another developer to run the project locally.
