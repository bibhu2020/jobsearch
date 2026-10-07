---
name: start
description: Learn the current repo, architecture, and constraints before making a change.
---

# Start

Use this skill before changing code, adding a feature, or refactoring anything in this repository.

## Goals
- Understand what the app does today.
- Identify the affected layer: frontend, gateway, Python agents, database, or deployment.
- Confirm the current commands, conventions, and environment assumptions.

## Required read order
1. Read [CLAUDE.md](../../CLAUDE.md) for repo-level architecture and workflow guidance.
2. Read [README.md](../../README.md) for product summary and deployment notes.
3. Read [package.json](../../package.json) for how the project runs and builds.
4. Read [pyproject.toml](../../pyproject.toml) for Python agent dependencies.
5. Read the relevant feature files for the change area only.

## Must-check facts
- The app is a full-stack job tracker with a Vue frontend, NestJS gateway, and Python/FastAPI agents.
- Local dev runs via `npm start`; production builds with `npm run build`.
- Database behavior is split: gateway uses PostgreSQL via `DATABASE_URL`; local agent work may use SQLite.
- AI routing is configurable through environment variables and supports Google/OpenAI/OpenRouter.

## Authoring rule
Do not start by editing code. First identify the real root cause, the affected module, and the user-facing behavior.

## Output expectations
Summarize:
- what the app currently does,
- what the change likely affects,
- which files to inspect next,
- any constraints from environment, auth, DB, or external services.
