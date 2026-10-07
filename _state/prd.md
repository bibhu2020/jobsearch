# PRD

## Product goal
Help job seekers organize applications, evaluate fit against roles, and generate useful AI-assisted artifacts to improve their job search process.

## Target users
- Active job seekers managing many applications
- Candidates who want ranking feedback and role alignment insights
- Users who want to generate cover letters, one-page profiles, and interview prep from their resume
- Hiring managers or interviewers in a secondary mode

## User stories
- As a candidate, I want to add a job to my pipeline so I can track it.
- As a candidate, I want to see each job’s fit score and reasoning so that I understand whether it is worth applying.
- As a candidate, I want to upload my resume and profile so that AI tools can tailor materials to the role.
- As a candidate, I want to generate cover letters and kits without leaving the app.
- As a candidate, I want to trigger job suggestions from search sources and ingest them into my pipeline.
- As an interviewer, I want a separate workflow for reviewing candidate and role information.

## Functional requirements
1. Authentication and per-user data access
2. Job creation from URL or raw text
3. Pipeline stage management and job tracking
4. Resume/profile ingestion and analysis
5. AI-based match scoring and recommendation
6. AI generation of cover letters and document kits
7. Export of PDFs and saved artifacts
8. Workflow-triggered job search and result import
9. GitHub-backed artifact and result storage

## Non-functional requirements
- Secure auth and scoped access
- Clear error handling for AI provider outages
- Fast enough UI feedback for job search and generation flows
- Remote-friendly architecture that works in dev and deployment environments

## Success metrics
- User can add and track jobs without friction.
- Job-fit recommendations are actionable and consistently above threshold.
- Generated kits are tailored to the profile and role.
- Job search suggestions are importable into the UI with minimal manual intervention.

## Risks and constraints
- AI provider rate limits or outages can affect generation and scoring.
- Country/remote restrictions must be treated correctly for candidate fit.
- GitHub storage and workflow calls require valid tokens and repo configuration.
- The app must avoid cross-user data leakage.
