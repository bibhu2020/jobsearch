---
name: spec
description: Define technical specifications for implementation.
---

# Spec

Use this skill to convert requirements into implementation-ready technical design.

## Spec sections
- Overview and architecture impact
- Frontend changes
- Backend API changes
- Agent changes
- Database schema or query changes
- External integrations and env vars
- Error handling and edge cases
- Test plan
- Rollback / backward compatibility

## For this codebase, always check
- Vue frontend components and stores
- NestJS modules under `services/gateway/src/`
- FastAPI routes in `agents/`
- SQL schema under `shared/`
- env variable requirements in `.env`

## Implementation rules
- Prefer the existing patterns and naming conventions.
- Reuse user-scoped queries and auth checks.
- Keep AI provider routing centralized.
- Preserve compatibility with the gateway → agents architecture.

## Deliverable
A technical specification that lists relevant files, data models, and behavior expectations in enough detail to implement without guesswork.
