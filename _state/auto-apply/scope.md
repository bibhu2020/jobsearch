# Scope — Auto-Apply

## Summary
Add an **Apply** button to Wishlist cards on the pipeline board. Clicking it launches a browser
agent (Playwright, in the Python agents service) that opens the job's application page, fills
the form from the user's profile, creates a job-site account when required, completes email
verification through the user's Gmail, and **submits automatically** when every field could be
filled confidently. Anything it cannot handle pauses in a live view where the user can take over.
On success the card moves to **Applied** with a full record of what was submitted.

## User value
Applying is the most repetitive step in the job hunt (same name, email, resume, work-authorization
answers, again and again). Auto-apply turns "found a good job" into "applied" in one click.

## Affected user journeys
- Pipeline → Wishlist card → **Apply** → live view → (auto-submitted | review → Submit | take over) → card in Applied.
- Profile → new **Auto-Apply** section: job-portal password, application defaults, auto-submit toggle,
  Easy Apply daily cap, Connect Gmail, Connect LinkedIn / Indeed.
- Job detail modal → **Application** tab: status, answers sent, screenshots.

## Impacted subsystems
| Subsystem | Change |
|---|---|
| frontend | Apply button on `JobCard` (wishlist only), `ApplyLiveModal`, Auto-Apply profile section, application record in `JobDetailModal`, `apply` Pinia store |
| gateway | New `apply` module (start/status/input/submit/cancel, background run tracker, cap enforcement), new `integrations` module (Gmail OAuth, site sessions), `crypto` service (AES-256-GCM) |
| agents | New `agents/apply/` package: run manager, form extraction + LLM answering, ATS handlers, Gmail reader, confidence gate |
| database | New tables `user_apply_settings`, `user_site_sessions`, `ats_accounts`, `application_runs` |
| storage | Confirmation screenshots stored in Postgres (`application_runs.screenshot`), not the GitHub artifacts repo — they contain personal answers |
| deploy | Same single container (HF Space). Needs Gmail OAuth client + encryption key secrets |

## In scope (all phases)
1. **Foundation** — encrypted credential store, application defaults, auto-submit toggle, Gmail connect,
   Apply button, live view with take-over, confidence gate, Greenhouse / Lever / Ashby handlers.
2. **LinkedIn & Indeed** — one-time sign-in via live view (session cookies saved encrypted), Easy Apply
   handlers, 5/day cap with spacing, follow "apply on company site" links to the employer's site.
3. **Account-based sites** — sign up / sign in with login email + portal password, email verification
   via Gmail, Workday and iCIMS / Taleo handlers.
4. **Generic career pages** — LLM-driven handler for any other site.

## Out of scope
- Solving or bypassing CAPTCHAs (always handed to the user).
- Hiding the automation from bot detection (browser-fingerprint spoofing, proxy rotation).
- Storing LinkedIn / Indeed passwords (sessions only).
- Bulk "apply to all" / scheduled auto-apply; one card at a time, user-initiated.
- Interviewer mode.

## Dependencies
- Google Cloud OAuth client (Gmail API, `gmail.readonly`), in "testing" mode (≤100 test users).
- `CREDENTIALS_ENC_KEY` secret.
- Chromium in the container (already present for PDF export).
- Existing kits: tailored resume / cover letter used when present.

## Risks & constraints
- **LinkedIn / Indeed terms of service prohibit automation; the user's own account may be restricted.**
  Accepted by the product owner; mitigated by the 5/day cap and spacing, not by hiding the automation.
- Job-site page layouts change; handlers will need maintenance.
- Datacenter IP (HF Space) triggers more security checks than a home connection.
- Irreversible action: a wrong auto-submitted answer reaches the employer. Mitigated by the confidence
  gate, the auto-submit toggle, and the full submission record.
- HF Space has limited memory: cap concurrent browsers.
- HF Space disk is ephemeral: all state (sessions, run results) must live in Postgres / GitHub.

## Product-level acceptance criteria
- Apply button appears only on Wishlist cards.
- For a Greenhouse / Lever / Ashby posting with all answers known, the application is submitted
  without user interaction and the card moves to Applied.
- When any answer is uncertain, a CAPTCHA appears, or auto-submit is off, the run pauses and the user
  can review, edit via take-over, and submit or cancel.
- Account creation uses the login email + portal password; verification emails are read from Gmail.
- LinkedIn / Indeed Easy Apply submits at most 5 per rolling 24h per user.
- Every submitted application is recorded with its answers and a confirmation screenshot.
- Secrets (portal password, Gmail token, site sessions) are encrypted at rest and never returned to the browser.
