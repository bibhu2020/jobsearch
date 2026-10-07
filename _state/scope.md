# Scope

## Product summary
Linear Lantern is a full-stack job application tracker designed for candidates to manage applications, review fit, and generate AI-assisted job materials. It also includes an interviewer mode that is not yet fully developed.

## Core workflow
- Users authenticate to a private dashboard.
- They add jobs manually by URL or raw text.
- Jobs are stored in a user-scoped pipeline and grouped by status.
- AI agents score and rank jobs against a user's profile.
- Users can generate and save cover letters, career kit documents, and related materials.
- Users can trigger GitHub Actions job search tasks and import suggestions back into the application.

## In-scope subsystems
- Frontend: Vue 3 + Vite + Tailwind UI
- Gateway: NestJS REST API and authentication
- Agents: FastAPI AI services for search, generation, resume parsing, PDF export
- Database: PostgreSQL in production, SQLite for local agent/dev work
- Storage: GitHub-backed artifact storage for resumes/PDFs and workflow outputs

## Out of scope or partially implemented
- Interviewer mode is present in the codebase but is still under development.
- Some AI features are provider-configurable and may vary by environment.
- GitHub Actions job search is user-triggered, not scheduled.

## Current app boundaries
- User-specific access is enforced with `user_id` scoping in DB queries.
- Route protection is enforced for authenticated API flows.
- External services include GitHub, OpenAI, Google Gemini, and OpenRouter.

## Key constraints
- Must maintain private user data isolation.
- AI services must gracefully degrade when providers fail.
- File storage must work via GitHub repo contents API instead of local filesystem.
- Local dev and production should share a similar architecture but use different database backends.
