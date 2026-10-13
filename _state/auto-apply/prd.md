# PRD — Auto-Apply

## 1. Problem statement
Candidates spend most of their application time re-typing the same information into different job
sites, creating throwaway accounts, and clicking verification emails. Linear Lantern already knows the
candidate's profile, resume and tailored documents but stops at "Wishlist" — the user still has to
apply by hand.

## 2. Target users
Candidate-mode users with an uploaded resume and analyzed profile, applying to roles found via the
suggestions agent or added manually (LinkedIn, Indeed, company ATS links).

## 3. User stories
1. As a candidate, I click **Apply** on a Wishlist card and the application is submitted for me, so the
   card moves to Applied without me touching the job site.
2. As a candidate, when the agent isn't sure about an answer, it stops and shows me what it filled so I
   can correct it before anything is sent.
3. As a candidate, I can watch the agent work and **take over** the browser (click/type) at any point.
4. As a candidate, I set my standard answers once (work authorization, sponsorship, salary, notice
   period, relocation, demographics, links) and they are reused everywhere.
5. As a candidate, I set one job-portal password; the agent uses it with my login email for every site
   that needs an account, and logs into accounts it created before.
6. As a candidate, I connect Gmail once so the agent can complete email verification by itself.
7. As a candidate, I sign in to LinkedIn and Indeed once (inside the live view) and the agent uses Easy
   Apply for me, at most 5 times a day.
8. As a candidate, I can turn auto-submit off to review every application before it is sent.
9. As a candidate, I can open any applied card and see exactly what was submitted.

## 4. Business goals
- Cut time-to-apply per job from ~10–20 min to under 2 min of user attention.
- Increase the share of Wishlist cards that reach Applied.

## 5. Functional requirements

### Apply button & runs
- FR-1 Apply button is shown on Wishlist cards only; clicking it does not open the card detail.
- FR-2 Starting a run requires: resume uploaded, portal password set, application defaults saved
  (required subset: full name, phone, work authorization, sponsorship). Missing items → message linking to Profile.
- FR-3 One active run per user. Starting another while one is active returns the active run.
- FR-4 Run statuses: `queued → running → (needs_input | awaiting_review) → submitting → submitted`,
  or `failed` / `cancelled`. Every status change is visible in the live view.
- FR-5 Live view shows the latest browser screenshot (≈1–2 s refresh), a step log, and the current
  status, and offers **Take over** (click and type on the screenshot), **Resume agent**, **Submit**
  (when awaiting review) and **Cancel**.
- FR-6 Closing the live view does not stop the run; reopening the card's Apply button reattaches.
- FR-7 Run idle for 10 min in `needs_input` / `awaiting_review` is cancelled.

### Filling & submitting
- FR-8 Answers come, in priority order, from: application defaults → profile/resume → LLM inferred from
  resume and job description. Each answer carries a source and confidence.
- FR-9 Resume upload uses the card's tailored resume PDF if a `resume` kit exists, otherwise the
  uploaded resume file. Cover letter fields use the `cover_letter` kit if present, otherwise an
  LLM-generated short letter.
- FR-10 **Auto-submit gate**: submit without the user only when auto-submit is ON and all of:
  every required field filled; no answer below the confidence threshold (0.8) or from LLM on a
  legal/attestation question (work authorization, sponsorship, criminal history, demographics,
  "I certify…"); file uploads confirmed; no CAPTCHA; no validation errors after the final fill.
  Otherwise status `awaiting_review` (or `needs_input` for CAPTCHA / unknown page).
- FR-11 Success is confirmed by detecting a confirmation page/message; card moves to Applied with the
  confirmation screenshot attached. If submission cannot be confirmed, status `failed` with
  "Submitted — confirmation not detected" so the user can check.

### Accounts & verification
- FR-12 Sites requiring an account: try sign-in with login email + portal password first (if an
  `ats_accounts` row exists for the tenant), else sign up. Record the tenant on success.
- FR-13 Email verification: poll Gmail (read-only) for up to 3 min for a message from the site's domain
  received after the run started; extract a code or verification link and apply it.
- FR-14 Password-rule rejection (site requires a different format) → `needs_input` with explanation.

### LinkedIn / Indeed
- FR-15 Connect LinkedIn / Indeed from Profile opens a live view on the site's login page; the user signs
  in; the session is saved encrypted. Expired sessions prompt reconnect.
- FR-16 If the posting has an external "Apply on company website" link, follow it and use the matching
  handler instead of Easy Apply.
- FR-17 Easy Apply submissions limited to the user's cap (default 5, per rolling 24h) and at least
  3 minutes apart; over-cap starts are refused with the time the next slot opens.

### Profile settings
- FR-18 New **Auto-Apply** profile section: portal password (write-only, shows "set"/"not set"),
  auto-submit toggle (default ON), Easy Apply daily cap (default 5, max 5), Gmail connection status,
  LinkedIn / Indeed connection status, application defaults form.
- FR-19 Application defaults: full legal name, preferred name, phone, address (city/state/country/zip),
  LinkedIn, GitHub, portfolio, work authorized countries, requires sponsorship (Y/N), earliest start /
  notice period, salary expectation (amount + currency), willing to relocate, remote preference,
  years of experience, highest education, gender / race / veteran / disability (each defaulting to
  "Decline to answer"), plus free-form custom Q&A pairs.

### Records
- FR-20 Job detail modal shows the latest application run: status, site, auto/review submitted,
  list of question → answer (source), screenshots, timestamps.

## 6. Non-functional requirements
- Security: portal password, Gmail refresh token and site sessions encrypted with AES-256-GCM using
  `CREDENTIALS_ENC_KEY`; never returned by any API; never logged; agents receive them only for the
  duration of a run over the internal localhost link.
- Isolation: every query scoped by `user_id`; one user's run cannot be read or controlled by another.
- Resource: max 2 concurrent browser runs per container; runs beyond that queue.
- Resilience: AI provider failures fall back as elsewhere; a crashed run ends `failed` with a message,
  never leaves the card in a wrong stage.
- Gmail access limited to `gmail.readonly`; queries filtered by sender domain and time window.

## 7. Success metrics
- ≥70% of Greenhouse/Lever/Ashby runs auto-submit without user input (once defaults are filled).
- ≥90% of runs end in a terminal state (no stuck runs).
- Zero secrets present in logs or API responses (verified in review).

## 8. Risks / edge cases
- LinkedIn / Indeed account restriction (accepted risk; capped).
- Multi-page forms, conditional questions appearing after earlier answers.
- Dropdowns with no matching option → low confidence → review.
- Job posting closed / 404 → `failed` "Posting no longer accepting applications".
- Duplicate application (site says already applied) → treat as success, mark "already applied".
- CAPTCHA mid-run → `needs_input`, user solves via take-over, then **Resume agent**.
- Container restart mid-run → run marked `failed` on gateway restart ("interrupted").

## 9. Open questions
- Should the Easy Apply cap use the user's local day instead of rolling 24h? (Rolling 24h for now.)
- Should rejected-by-review answers be learned into custom Q&A automatically? (Later.)
