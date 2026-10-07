# Spec

## System overview
Linear Lantern is composed of three primary layers:

1. Frontend: Vue 3 app for the user experience
2. Gateway: NestJS API for auth, profiles, jobs, pipeline, suggestions, and GitHub interactions
3. Agents: Python/FastAPI service for AI-driven tasks such as resume analysis, job search, generation, and PDF export

## Frontend responsibilities
- Render auth screens and protected app views
- Manage user state with Pinia stores
- Display pipeline columns and job cards
- Trigger generation flows and suggestions import
- Handle jobs, profiles, and kit generation via gateway endpoints

## Gateway responsibilities
- Authenticate users
- Store and retrieve user-scoped data
- Proxy requests to Python agents where needed
- Manage GitHub artifact upload and workflow dispatch
- Expose consistent REST endpoints for frontend use

## Agent responsibilities
- Resume/profile analysis
- Job search orchestration across multiple sources
- AI-based job matching and recommendation
- Document generation (cover letters, interview questions, company briefs)
- PDF rendering from HTML templates
- Structured extraction from job descriptions and resumes

## Data model summary
Core tables include:
- `users`
- `user_profiles`
- `jobs`
- `pipeline_cards`
- `generated_kits`
- `job_suggestions`

All non-user tables are user-scoped via `user_id`.

## API and integration patterns
- Frontend calls the NestJS gateway through `/api` routes.
- The gateway is the only authenticated entry point.
- Python agent calls are routed through the gateway or directly by the workflow service when appropriate.
- AI provider selection is env-driven and should keep a fallback pattern for resilience.

## External integrations
- PostgreSQL for production gateway data
- SQLite for local Python agent dev use
- GitHub API for file storage and workflow dispatch
- OpenAI, Gemini, and OpenRouter for AI features
- Playwright for PDF generation
- Search sources for remote job discovery (e.g. Remotive, RemoteOK, Indeed, etc.)

## UI behavior expectations
- The dashboard is pipeline-centric.
- Users can move jobs among stages.
- Suggestions and generated documents appear near the relevant job context.
- Mobile support is present and includes a fixed bottom navigation pattern.

## Error-handling expectations
- AI provider fallback should not crash the entire app on a single exception.
- Missing or invalid GitHub content should fail gracefully and surface a clear message.
- Search result ingestion should ignore stale or duplicate suggestions.
- UI should handle auth errors by redirecting or clearing session state.

## Test and validation expectations
- Validate new features in the relevant route or page flow.
- Confirm backend auth and user scoping remain intact.
- Verify DB writes are still scoped to the current user.
- Check AI generation and matching flows for graceful degradation when provider keys fail.

## Known project assumptions
- Candidate mode is the primary supported mode.
- Interviewer mode exists but is still in-progress.
- GitHub-based artifact storage is a design requirement, not a local-file dependency.
- The repo should retain the local `local` → `main` merge workflow.
