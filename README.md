---
title: Linear Lantern
emoji: 🪔
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# Linear Lantern — Job Application Tracker

A full-stack Kanban job tracker with AI-powered document generation and automated job search across 10 sources.

## HF Space

`https://huggingface.co/spaces/mishrabp/jobsearch`

## Secrets required (Space Settings → Variables and secrets)

| Secret | Source in `.env` | Description |
|---|---|---|
| `DATABASE_URL` | `.env` | Neon PostgreSQL connection string |
| `GITHUB_TOKEN` | `.env` | GitHub PAT with `repo` scope |
| `GITHUB_ARTIFACTS_PATH` | `.env` | GitHub folder URL for resumes/PDFs |
| `OPENAI_API_KEY` | `.env` | OpenAI key (GPT-4o fallback) |
| `GEMINI_API_KEY` | `.env` | Google Gemini key (primary AI) |
| `JWT_SECRET` | `.env` | Long random string for auth tokens |

`AGENTS_URL` and `PORT` are set automatically inside the container — do not override them as secrets.
