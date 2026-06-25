# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Linear Lantern — Job Application Tracker

A full-stack job application tracker with a Kanban pipeline board, AI-powered document generation, and a user-triggered GitHub Actions job search agent. Two modes: **Candidate** (default — job hunting) and **Interviewer** (hiring managers, in development).

## Setup & Commands

```bash
# Production setup — PostgreSQL (DATABASE_URL required)
npm run setup          # npm install + pip install + playwright + init-pg.js

# Local dev setup — SQLite (no external DB needed)
npm run setup:local    # npm install + pip install + playwright + init-db.js

# Start all 3 services (gateway :3000, agents :8000, frontend :5173)
npm start

# Build for production
npm run build

# Re-apply PostgreSQL schema (idempotent)
npm run db:init        # node shared/init-pg.js
```

`npm start` uses `concurrently` to launch:
- **Gateway** (NestJS): `nest start --watch`
- **Agents** (Python/FastAPI): `PYTHONPATH=. uvicorn agents.main:app --reload --port 8000`
- **Frontend** (Vue/Vite): `vite --config frontend/vite.config.ts`

## Architecture

```
Frontend (Vue 3, :5173)
    ↓ /api proxy
Gateway (NestJS, :3000)   ←→   Agents (Python FastAPI, :8000)
    ↓
PostgreSQL (DATABASE_URL)      ← production
SQLite (shared/job_tracker.db) ← local Python agent dev only
```

**Dual-database**: The NestJS gateway always uses PostgreSQL via `DATABASE_URL`. Python agents use `aiosqlite` against the local SQLite file for local dev; in GitHub Actions, `run_search.py` reads entirely from env vars and writes results to the repo (no DB access needed).

`database.service.ts` auto-converts SQLite-style `?` placeholders to PostgreSQL `$1 $2 ...` via its `pgify()` method, so all query strings use `?` throughout the gateway codebase.

### Services

| Directory | Tech | Port | Responsibility |
|---|---|---|---|
| `frontend/` | Vue 3 + Vite + Tailwind | 5173 | UI — Kanban board, modals, views |
| `services/gateway/src/` | NestJS (TypeScript) | 3000 | Auth, job tracker CRUD, proxy to agents |
| `agents/` | Python FastAPI | 8000 | All AI work: profile analysis, generation, PDF, search |

### Gateway modules (`services/gateway/src/`)
- `auth/` — JWT register/login (bcryptjs + passport-jwt)
- `profile/` — Profile CRUD + resume upload + proxy to `/profile/analyze`
- `jobs/` — Add job by URL (cheerio scrape) or text (agents extract)
- `pipeline/` — Kanban card CRUD + stage/position moves
- `kits/` — Generate/save/download AI kits (proxy to agents)
- `suggestions/` — Job suggestions: trigger GitHub Actions, poll run status, import results
- `github-storage/` — File uploads (resumes, PDFs) stored as GitHub repo contents via API

All routes prefixed with `/api`. Protected by `JwtAuthGuard` except `/api/auth/*`.

### Python agents (`agents/`)
- `main.py` — FastAPI app; registers all routers
- `profile_agent.py` — Resume text analysis via OpenAI
- `generate_agent.py` — Cover letter, resume rewrite, interview Qs, company brief (gpt-4o → Gemini fallback)
- `pdf_agent.py` — Playwright HTML→PDF using Jinja2 templates in `agents/templates/`
- `search_agent.py` — Orchestrates 10 parallel sources + OpenAI scoring (only returns `match_score >= 70`)
- `jobs_agent.py` — Extracts structured job info from raw content
- `sources/` — 10 active sources: remotive, remoteok, weworkremotely, linkedin, indeed, dice, builtin, wellfound, remote100k, remoterocketship
- `run_search.py` — Standalone script for GitHub Actions; reads all config from env vars, writes `search_results/{user_id}/YYYY-MM-DD.json`

### Frontend (`frontend/src/`)
- `stores/` — Pinia: auth, pipeline, suggestions, profile
- `views/` — PipelineView, SuggestionsView, ProfileView, Login/Register
- `components/` — KanbanBoard → KanbanColumn (vue-draggable-plus) → JobCard; JobDetailModal → GenerateKitPanel; AddJobModal; SuggestionCard; BottomNav (mobile-only fixed footer nav)
- `api/index.ts` — Axios instance with JWT interceptor + 401 redirect

**Mobile nav**: `BottomNav.vue` is `sm:hidden fixed bottom-0` — shown only on mobile. `App.vue` mounts it globally when authenticated. Views with scroll areas use `pb-24 sm:pb-6` to avoid content hiding behind it.

## Database Schema

Schema files:
- `shared/schema.pg.sql` — PostgreSQL (used by `init-pg.js` for production)
- `shared/init.sql` — SQLite (used by `init-db.js` for local dev)

6 tables: `users`, `user_profiles`, `jobs`, `pipeline_cards`, `generated_kits`, `job_suggestions`.

All data is user-scoped: every table (except `users`) has `user_id` FK. All gateway queries and mutations include `user_id` in WHERE clauses.

## Python Dependencies

All Python deps in root `pyproject.toml`. Install with `pip install .`. The `npm start` script sets `PYTHONPATH=.` so the `agents` package is importable without an editable install.

## Key Environment Variables (`.env`)

```
# Database
DATABASE_URL=postgresql://...          # PostgreSQL connection string (gateway)
# DATABASE_PATH=./shared/job_tracker.db # SQLite path (local Python agents only)

# Services
AGENTS_URL=http://localhost:8000
JWT_SECRET=...
VITE_API_URL=http://localhost:3000

# AI
OPENAI_API_KEY=...
GEMINI_API_KEY=...

# GitHub (file storage + workflow dispatch)
GITHUB_TOKEN=...                       # PAT with repo + workflow scopes
GITHUB_WORKFLOW_REPO=owner/repo        # e.g. username/linear-lantern
GITHUB_BRANCH=main
```

## File Storage

All files stored in the GitHub repo via the contents API (no local filesystem dependency):
- Uploaded resumes → `artifacts/resumes/{userId}/resume.{ext}` (GitHub raw URL saved in DB)
- Generated PDFs → `artifacts/generated/{userId}/{cardId}/{type}.pdf` (GitHub raw URL saved in DB)
- Job search results → `search_results/{userId}/YYYY-MM-DD.json` (committed by GitHub Actions)

## GitHub Actions Job Search

`.github/workflows/job-search.yml` — **user-triggered only** (`workflow_dispatch`; no cron schedule).

Triggered from the UI via `POST /api/suggestions/trigger-action`. The gateway:
1. Fetches the user's profile from DB
2. Dispatches the workflow with `user_id`, `profile_summary`, `skills`, `experience`, `keywords`, `location` as inputs
3. Returns immediately; frontend polls `GET /api/suggestions/workflow-run` for live status

`run_search.py` reads all config from env vars (`USER_ID`, `PROFILE_SUMMARY`, `SKILLS`, `EXPERIENCE`, `SEARCH_KEYWORDS`, `SEARCH_LOCATION`). Results committed to `search_results/{user_id}/YYYY-MM-DD.json`.

On workflow completion, the frontend auto-triggers `POST /api/suggestions/import`, which reads the latest result file from GitHub contents API (not local filesystem), dismisses stale `pending` suggestions, and upserts new ones.

Requires GitHub Secrets: `OPENAI_API_KEY`, `GEMINI_API_KEY`.

## Git Workflow

**Always develop on the `local` branch. Never commit directly to `main`. Open a PR to merge `local` → `main`.**
