---
name: ship
description: Prepare a change for release, deployment, and handoff.
---

# Ship

Use this skill when the implementation is complete and ready to release.

## Ship checklist
- Verify build and runtime checks pass.
- Confirm env variables and secret assumptions are documented.
- Check database and migration compatibility.
- Review API, frontend, and AI changes for regressions.
- Ensure branch workflow is respected.

## Repository workflow
- Work on `local` while developing.
- Merge `local` into `main` only through a clean PR or merge flow.
- Do not commit directly to `main`.

## Deployment readiness
- Confirm needed secrets exist in the target environment.
- Ensure GitHub file storage paths remain valid.
- Validate AI provider configuration and fallback behavior.
- Check that any new external dependency is accounted for in local and production setup.

## Release note guidance
Capture:
- what changed,
- why it matters,
- which environment variables or config are required,
- any follow-up tasks or rollback notes.
