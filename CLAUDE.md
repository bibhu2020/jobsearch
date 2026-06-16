# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Linear Lantern — Job Application Tracker

A full-stack job application tracker with a Kanban pipeline board, AI-powered document generation, and a weekly automated job search agent.

## Setup & Commands

```bash
# First-time setup (installs all deps + initializes SQLite DB)
npm run setup

# Start all 3 services (gateway :3000, agents :8000, frontend :5173)
npm start

# Build for production
npm run build
```

`npm start` uses `concurrently` to launch:
- **Gateway** (NestJS): `nest start --watch`
- **Agents** (Python/FastAPI): `uvicorn agents.main:app --reload --port 8000`
- **Frontend** (Vue/Vite): `vite --config frontend/vite.config.ts`

## Architecture

Three services sharing one SQLite database (`shared/job_tracker.db`):

```
Frontend (Vue 3, :5173)
    ↓ /api proxy
Gateway (NestJS, :3000)   ←→   Agents (Python FastAPI, :8000)
    ↓
SQLite (shared/job_tracker.db)
```

### Services

| Directory | Tech | Port | Responsibility |
|---|---|---|---|
| `frontend/` | Vue 3 + Vite + Tailwind | 5173 | UI — Kanban board, modals, views |
| `services/gateway/src/` | NestJS (TypeScript) | 3000 | Auth, job tracker CRUD, proxy to agents |
| `agents/` | Python FastAPI | 8000 | All AI work: profile analysis, generation, PDF, search |

### Gateway modules (`services/gateway/src/`)
- `auth/` — JWT register/login (bcryptjs + passport-jwt)
- `profile/` — Profile CRUD + resume upload (Multer) + proxy to `/profile/analyze`
- `jobs/` — Add job by URL (cheerio scrape) or text (agents extract)
- `pipeline/` — Kanban card CRUD + stage/position moves
- `kits/` — Generate/save/download AI kits (proxy to agents)
- `suggestions/` — Job suggestions from agent search results

All routes prefixed with `/api`. Protected by `JwtAuthGuard` except `/api/auth/*`.

### Python agents (`agents/`)
- `main.py` — FastAPI app; registers all routers
- `profile_agent.py` — Resume text analysis via OpenAI
- `generate_agent.py` — Cover letter, resume rewrite, interview Qs, company brief (gpt-4o → Gemini fallback)
- `pdf_agent.py` — Playwright HTML→PDF using Jinja2 templates in `agents/templates/`
- `search_agent.py` — Orchestrates 5 parallel sources + OpenAI scoring
- `jobs_agent.py` — Extracts structured job info from raw content
- `sources/` — 5 independent search sources (remotive, arbeitnow, ddg, indeed_rss, google_pw)
- `run_search.py` — Standalone script called by GitHub Actions every Friday night

### Frontend (`frontend/src/`)
- `stores/` — Pinia: auth, pipeline, suggestions, profile
- `views/` — PipelineView, SuggestionsView, ProfileView, Login/Register
- `components/` — KanbanBoard → KanbanColumn (vue-draggable-plus) → JobCard; JobDetailModal → GenerateKitPanel; AddJobModal; SuggestionCard
- `api/index.ts` — Axios instance with JWT interceptor + 401 redirect

## Database Schema

6 tables in `shared/init.sql`: `users`, `user_profiles`, `jobs`, `pipeline_cards`, `generated_kits`, `job_suggestions`. Run `node shared/init-db.js` to initialize.

## Python Dependencies

All Python deps in root `pyproject.toml`. Install with `pip install .` (non-editable; editable mode requires newer pip). The `npm start` script sets `PYTHONPATH=.` so the `agents` package is importable without an editable install.

## Key environment variables (`.env`)

```
DATABASE_PATH=./shared/job_tracker.db
ARTIFACTS_PATH=./artifacts
AGENTS_URL=http://localhost:8000
JWT_SECRET=...
OPENAI_API_KEY=...
GEMINI_API_KEY=...
VITE_API_URL=http://localhost:3000
```

## File storage

- Uploaded resumes → `artifacts/resumes/{userId}/resume.{ext}`
- Generated PDFs → `artifacts/generated/{userId}/{cardId}/{type}.pdf`
- Weekly search results → `search_results/YYYY-MM-DD.json`

## GitHub Actions

`.github/workflows/job-search.yml` runs every Friday 8 PM UTC. Requires GitHub Secrets: `OPENAI_API_KEY`, `GEMINI_API_KEY`. Results committed to `search_results/` and importable via the Suggestions page "Find New Jobs" button.
