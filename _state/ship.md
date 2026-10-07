# Ship

## Deployment model
This repository is designed to run in a full-stack environment with:
- a NestJS backend,
- a Python agent service,
- a Vue frontend,
- PostgreSQL in production,
- GitHub-backed file storage and workflow automation.

## Required environment variables
Key values must be present in the environment, typically via `.env` for local development and secrets for deployment:
- `DATABASE_URL`
- `AGENTS_URL`
- `JWT_SECRET`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY` (if using OpenRouter fallback)
- `GITHUB_TOKEN`
- `GITHUB_WORKFLOW_REPO`
- `GITHUB_BRANCH`
- AI provider settings such as `AI_PRIMARY_PROVIDER`, `AI_FALLBACK_PROVIDER`, `OPENROUTER_MODEL`

## Branch policy
- Default development should occur on `local`.
- Merge changes into `main` only through a reviewed, clean merge flow.
- Do not commit directly to `main` as a normal workflow.

## Release checklist
- Confirm all required env vars and secrets exist.
- Validate the project builds with `npm run build`.
- Confirm the app boots with `npm start` or equivalent in the target environment.
- Ensure GitHub repo storage paths and workflows remain valid.
- Verify AI provider routing matches the intended primary/fallback behavior.
- Check that user-specific data remains correctly isolated.

## Rollback guidance
If a release fails:
- revert the offending merge or commit,
- restore prior environment variables,
- recheck GitHub Actions and artifact paths,
- confirm no DB schema mismatches or auth regressions remain.
