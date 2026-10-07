---
name: scope
description: Define the project scope for a new feature or change request.
---

# Scope

Use this skill to capture the scope of a feature before implementation.

## Scope checklist
- Product goal
- User value
- Affected user journey(s)
- Affected subsystems:
  - frontend
  - gateway
  - agents
  - database
  - GitHub Actions / storage
- Non-goals and exclusions
- Risks and constraints
- Rollout/launch considerations

## Questions to answer
1. What user problem does this solve?
2. Who is impacted?
3. What screens, actions, or workflows change?
4. Which APIs or DB tables must change?
5. Does this affect AI generation, search, or storage?
6. Which env vars or secrets are needed?
7. Does this introduce migration, deployment, or operational risk?

## Deliverable
Write a concise scope statement that includes:
- feature summary,
- in-scope items,
- out-of-scope items,
- dependencies,
- acceptance criteria at a business level.

## Guardrails
- Do not assume hidden requirements.
- Separate product scope from technical implementation detail.
- Record the current project assumptions from the repo state before finalizing scope.
