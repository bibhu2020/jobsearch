---
name: prd
description: Capture product requirements and user-facing expectations.
---

# PRD

Use this skill to turn a feature idea into clear product requirements.

## PRD structure
1. Problem statement
2. Target users
3. User stories
4. Business goals
5. Functional requirements
6. Non-functional requirements
7. Success metrics
8. Risks / edge cases
9. Open questions

## Product expectations
For this project, requirements should reflect:
- Candidate job-hunting workflow
- Interviewer workflow (in development)
- AI-generated artifacts and job-fit recommendations
- Kanban job pipeline management
- Secure auth and scoped user data
- GitHub-backed file storage and workflow integration

## Acceptance criteria guidance
Every requirement should be testable and user-visible. Prefer statements like:
- "When a user adds a job, it is stored under their user_id and appears in the pipeline."
- "When the user triggers job search, the system returns ranked matches above threshold."

## Rule
Keep the PRD product-facing. Avoid implementation-specific language unless it is directly needed to explain constraints.
