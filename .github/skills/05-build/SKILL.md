---
name: build
description: Implement the approved design and validate it with the repo’s existing build/test flow.
---

# Build

Use this skill to implement changes using the current repo patterns.

## Working rules
- Start from the current architecture and file structure.
- Change the smallest relevant surface area.
- Keep user-scoped data access consistent.
- Prefer existing shared patterns for auth, storage, AI, and DB queries.

## Commands
- `npm start` for local development stack
- `npm run build` for production build validation
- `npm run setup:local` for local environment setup
- `npm run db:init` to reinitialize PostgreSQL schema when needed
- `python3 -m py_compile ...` for Python syntax checks if relevant

## Validation checklist
- Does the change compile in the relevant layer?
- Are API contracts maintained?
- Did the relevant UI state still work?
- Are AI or external integrations guarded by error handling?
- Are env vars and secrets documented?

## Rule
Do not claim a feature is complete until it has been validated in the relevant command path.
