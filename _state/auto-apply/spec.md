# Spec — Auto-Apply

Implements [prd.md](prd.md) within [scope.md](scope.md). Phase markers: **P1** foundation,
**P2** LinkedIn/Indeed, **P3** account sites, **P4** generic pages.

## 1. Architecture

```
Browser (Vue)                 Gateway (NestJS :3000/7860)             Agents (FastAPI 127.0.0.1:8000)
ApplyLiveModal ──poll 1.5s──▶ GET /api/apply/runs/:id ──proxy live──▶ GET /apply/runs/{id}
  click/type   ────────────▶ POST /api/apply/runs/:id/input ───────▶ POST /apply/runs/{id}/input
JobCard [Apply] ───────────▶ POST /api/apply/cards/:cardId/start
                                 │ load profile, defaults, decrypt secrets,
                                 │ fetch resume bytes, compute Easy Apply allowance
                                 ├─ INSERT application_runs (queued)
                                 ├─ POST /apply/runs  (secrets in body, localhost only) ─▶ RunManager
                                 └─ ApplyTracker polls agents every 3 s until terminal:  ├ asyncio task / run
                                      persist status, fields, new ats_accounts,          ├ Playwright Chromium
                                      session cookies; on submitted → upload screenshot, ├ handler (greenhouse…)
                                      move card to Applied                               └ screenshot loop 1 s
```

- The gateway stays the only authenticated entry point and the only DB writer. Agents keep run state
  in memory only and receive secrets per run.
- Agents bind to `127.0.0.1` in the container (`supervisord.conf`) because secrets now flow over that link.
- Max 2 concurrent browser runs per container (`APPLY_MAX_CONCURRENCY`, default 2); further runs wait in `queued`.

## 2. Database (`shared/schema.pg.sql`, mirrored in `shared/init.sql`)

```sql
CREATE TABLE IF NOT EXISTS user_apply_settings (
  user_id               INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  portal_password_enc   TEXT,                       -- AES-256-GCM
  auto_submit           BOOLEAN NOT NULL DEFAULT TRUE,
  easy_apply_daily_cap  INTEGER NOT NULL DEFAULT 5, -- 0..5
  defaults              TEXT    NOT NULL DEFAULT '{}', -- JSON, see §6
  gmail_refresh_token_enc TEXT,
  gmail_email           TEXT,
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_site_sessions (     -- P2: linkedin | indeed
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  site        TEXT    NOT NULL,
  state_enc   TEXT    NOT NULL,                     -- Playwright storage_state JSON, encrypted
  updated_at  TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, site)
);

CREATE TABLE IF NOT EXISTS ats_accounts (           -- P3: accounts the agent created/used
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tenant      TEXT    NOT NULL,                     -- e.g. "acme.wd5.myworkdayjobs.com"
  email       TEXT    NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, tenant)
);

CREATE TABLE IF NOT EXISTS application_runs (
  id               TEXT PRIMARY KEY,                -- uuid
  user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  pipeline_card_id INTEGER NOT NULL REFERENCES pipeline_cards(id) ON DELETE CASCADE,
  kind             TEXT NOT NULL DEFAULT 'apply',   -- apply | login
  status           TEXT NOT NULL DEFAULT 'queued',  -- queued|running|needs_input|awaiting_review|submitting|submitted|failed|cancelled
  site             TEXT,                            -- greenhouse|lever|ashby|linkedin|indeed|workday|icims|taleo|generic
  channel          TEXT,                            -- ats | easy_apply
  apply_url        TEXT,
  auto_submitted   BOOLEAN NOT NULL DEFAULT FALSE,
  message          TEXT,                            -- last human-readable status / error
  fields           TEXT NOT NULL DEFAULT '[]',      -- JSON FieldRecord[]
  screenshot       BYTEA,                           -- confirmation JPEG; kept in Postgres, never GitHub storage
  started_at       TIMESTAMPTZ DEFAULT NOW(),
  finished_at      TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_application_runs_user ON application_runs(user_id, started_at DESC);
```

`FieldRecord = { label, type, required, value, source: 'default'|'profile'|'llm'|'file'|'user', confidence, sensitive }`

## 3. Secrets — `services/gateway/src/crypto/crypto.service.ts` (global module)
- AES-256-GCM, key = base64 32 bytes from `CREDENTIALS_ENC_KEY`.
- Format `v1:<iv b64>:<tag b64>:<ciphertext b64>`; `encrypt(str)`, `decrypt(str)`.
- Missing key → `isConfigured() = false`; secret-saving endpoints return 503 "CREDENTIALS_ENC_KEY not configured".
- No API ever returns decrypted values; settings expose booleans (`portalPasswordSet`, `gmailConnected`, …).

## 4. Gateway API

### `apply` module (`services/gateway/src/apply/`) — all JwtAuthGuard
| Method | Path | Behaviour |
|---|---|---|
| GET | `/api/apply/settings` | `{ portalPasswordSet, autoSubmit, easyApplyDailyCap, defaults, gmail: {connected, email}, sites: {linkedin, indeed} }` |
| PUT | `/api/apply/settings` | body `{ portalPassword?, autoSubmit?, easyApplyDailyCap?, defaults? }`; upsert |
| POST | `/api/apply/cards/:cardId/start` | validate card is user's + `wishlist`; preflight (FR-2) → 400 `{missing:[…]}`; if active run exists return it; else create + dispatch → `{ runId }` |
| GET | `/api/apply/runs/active` | user's non-terminal run or `null` |
| GET | `/api/apply/runs/:runId` | DB row + live `{screenshot, log, step}` from agents when non-terminal |
| POST | `/api/apply/runs/:runId/input` | `{kind:'click',x,y} \| {kind:'type',text} \| {kind:'key',key} \| {kind:'scroll',dy}` |
| POST | `/api/apply/runs/:runId/verification` | `{value}` — code or link typed by the user when Gmail is unavailable (only while the run asks for it) |
| POST | `/api/apply/runs/:runId/{resume,submit,cancel,mark-applied}` | control; `mark-applied` = user applied manually via take-over |
| GET | `/api/apply/cards/:cardId/runs` | history for the card (no live data) |

`ApplyTracker` (in `apply.service.ts`): `Map<runId, Interval>`; polls agents every 3 s; writes `status, site, channel, apply_url, message, fields`; on agent-reported `new_accounts` → upsert `ats_accounts`; on `session_updates` → encrypt + upsert `user_site_sessions`; on terminal → stop polling, set `finished_at`; if `submitted` → store the final screenshot in `application_runs.screenshot` (served by auth-only `GET /api/apply/runs/:runId/screenshot`), move card to `applied` at end of column. Agent 404 for a non-terminal run → `failed` "Run lost (service restarted)". On module init: mark all non-terminal rows `failed` "Interrupted by restart".

Limits checked at start (after the active-run check), returning 429 with a readable message:
`APPLY_USER_DAILY_LIMIT` (default 25 runs started per user per 24 h), `APPLY_MAX_PENDING_RUNS` (default 10 unfinished runs
across all users). While `queued`, `GET /runs/:id` reports the number of queued runs ahead. Secrets that can't be decrypted
(key changed) → 400 asking to re-enter the portal password; Gmail / sessions treated as disconnected. Agent-reported
`gmail_invalid` → stored Gmail token cleared so Profile shows "Connect Gmail" again.

Easy Apply allowance (P2) computed at start — also refused when all users together reached `EASY_APPLY_GLOBAL_DAILY_CAP` (default 40/24 h, shared IP): submitted runs with `channel='easy_apply'` in last 24 h `< cap` and last one ≥ 3 min ago → passed to agents as `easy_apply: {allowed, reason}`.

### `integrations` module (`services/gateway/src/integrations/`)
| Method | Path | Behaviour |
|---|---|---|
| GET | `/api/integrations/gmail/auth-url` (guarded) | Google consent URL; `scope=gmail.readonly openid email`, `access_type=offline`, `prompt=consent`, `state` = JWT `{sub, purpose:'gmail'}` 10 min |
| GET | `/api/integrations/gmail/callback` (public) | verify state, exchange code, store encrypted refresh token + email; redirect `/profile?gmail=connected` (or `?gmail=error`) |
| DELETE | `/api/integrations/gmail` (guarded) | revoke token (best effort) + clear |
| POST | `/api/integrations/sites/:site/connect` (P2) | start `kind='login'` run on site login page; returns runId (uses the same live modal) |
| POST | `/api/apply/runs/:runId/finish-login` (P2) | agent captures storage_state → tracker saves session |
| DELETE | `/api/integrations/sites/:site` (P2) | delete session |

## 5. Agents (`agents/apply/`)

```
agents/apply/
  __init__.py
  router.py        FastAPI routes under /apply
  manager.py       RunManager (in-memory runs, semaphore, idle timeout), Run state, screenshot loop, control events
  forms.py         in-page field extraction (JS) + fill helpers (text, select, radio, checkbox, combobox, file)
  answers.py       defaults matcher (rules) → LLM answers with confidence; sensitive-question classifier
  gate.py          auto-submit decision (FR-10)
  detect.py        URL/page → handler; captcha + confirmation detectors
  gmail.py         (P1 module, used P3) refresh token → access token; poll for code/link
  handlers/
    base.py        Handler protocol + SinglePageFormHandler (navigate → fill → gate → submit → confirm)
    greenhouse.py  P1
    lever.py       P1
    ashby.py       P1
    linkedin.py    P2
    indeed.py      P2
    workday.py     P3
    icims.py       P3 (also taleo)
    generic.py     P4
```

### Agent API (internal)
- `POST /apply/runs` body:
  ```json
  { "run_id": "...", "kind": "apply",
    "job": {"url","title","company","description"},
    "applicant": {"email","password","name","profile":{...},"resume_text","defaults":{...}},
    "files": {"resume": {"filename","b64"}, "cover_letter_text": "..."},
    "settings": {"auto_submit": true},
    "easy_apply": {"allowed": true, "reason": ""},
    "gmail": {"refresh_token": "..."} | null,
    "sessions": {"linkedin": {...storage_state}} ,
    "known_accounts": ["tenant", ...] }
  ```
- `GET /apply/runs/{id}` → `{ status, site, channel, apply_url, step, message, log: [str], screenshot: "<b64 jpeg>", fields: FieldRecord[], new_accounts: [], session_updates: {} }`
- `POST /apply/runs/{id}/input|resume|submit|cancel|mark-applied|finish-login`

### Run lifecycle
1. `queued` until semaphore acquired → `running`. Launch Chromium (headless, viewport 1280×900, `storage_state` from sessions when relevant). Temp dir per run for the resume file; deleted at end.
2. `detect.resolve(url)` → handler. Unknown site in P1–P3 → `needs_input` "Unsupported site — take over and apply, then click Mark applied".
3. Handler navigates to the application form, calls `forms.extract(frame)` → field list, `answers.answer(fields, ctx)` → values, fills, re-extracts to catch conditional fields (max 3 passes).
4. `gate.decide()` → `submit` or `review(reasons)`. Review → `awaiting_review`, waits for `submit` / `cancel` / take-over + `resume`.
5. Submit → `submitting`; wait for confirmation (≤ 30 s). CAPTCHA challenge visible → `needs_input`. Validation errors → one auto-repair pass, then `awaiting_review`.
6. Confirmation → `submitted`, final screenshot kept. Not detected → `failed` "Submitted — confirmation not detected; please check".
7. Idle in `needs_input`/`awaiting_review` > 10 min → `cancelled`. Runs are kept in memory 15 min after terminal for the tracker to collect.

### Answering (`answers.py`)
- Rule pass on normalized label: name parts, email (login email), phone, location, LinkedIn/GitHub/portfolio URLs, work authorization, sponsorship, salary, notice/start date, relocation, years of experience, education, demographic (gender/race/ethnicity/veteran/disability), "how did you hear" (→ "Job board"), custom Q&A (fuzzy match). Source `default`, confidence 1.0; option-matching for selects (case-insensitive, contains, synonyms yes/no).
- Remaining fields → one `call_ai` JSON request with resume, job, defaults and field schema; returns `{value, confidence}` per field; options must be chosen verbatim. Source `llm`.
- Long-text "cover letter"/"why us" fields → cover letter kit text or LLM short answer (source `llm`, confidence 0.85).
- `sensitive = True` for legal/attestation/demographic labels; LLM answers to sensitive fields are capped at confidence 0.5 (forces review).
- File inputs labelled resume/CV → resume file; cover letter file input → skipped unless required (then render text to PDF via existing pdf export).

### Gate (`gate.py`) — `submit` only if
`auto_submit` and no required field empty and every `confidence ≥ 0.8` and no visible captcha and no form errors and all file inputs report a file.

### Detectors
- Captcha: visible iframe with src matching `recaptcha/api2/bframe|hcaptcha.com/captcha|challenges.cloudflare.com` with non-zero box.
- Confirmation: handler-specific URL/text checks, fallback regex `thank(s| you) for (applying|your application|submitting)|application (has been )?(submitted|received)`.

### Handlers (P1)
- **Greenhouse**: `boards.greenhouse.io/*/jobs/*`, `job-boards.greenhouse.io/*/jobs/*`, or any page with `#grnhse_iframe` / `gh_jid` param (form inside iframe — operate on frame). Submit `button[type=submit]`, `#submit_app`. Confirmation: URL `/confirmation` or text.
- **Lever**: `jobs.lever.co/{co}/{id}` → `/{id}/apply`. Submit `#btn-submit` / `button[type=submit]`. Confirmation: URL `/thanks`.
- **Ashby**: `jobs.ashbyhq.com/{co}/{id}` → `/{id}/application`. Submit button text "Submit Application". Confirmation text.

### Gmail (`gmail.py`)
`GOOGLE_OAUTH_CLIENT_ID/SECRET` from env; refresh → access token via `oauth2.googleapis.com/token`; `users.messages.list?q=from:({domain}) newer_than:1h`, keep messages with `internalDate ≥ run start`; parse body for 4–8 digit code near "code"/"verification", or first link containing `verify|confirm|activate`. Poll every 10 s, ≤ 3 min.
`verification.obtain_verification(run, sender_domain)`: Gmail first; when not connected, expired (`invalid_grant` → `gmail_invalid`)
or nothing arrives → `needs_input` with `needs = {kind: 'verification', email, sender}`; the live view shows a code/link field
(`POST /apply/runs/{id}/verification`). Resume without a value = user completed it via take-over → `{manual: true}`.

## 6. Application defaults JSON
```json
{ "firstName": "", "lastName": "", "preferredName": "", "phone": "",
  "city": "", "state": "", "country": "", "postalCode": "",
  "linkedinUrl": "", "githubUrl": "", "portfolioUrl": "",
  "workAuthorizedCountries": ["United States"], "requiresSponsorship": false,
  "noticePeriod": "2 weeks", "earliestStartDate": "",
  "salaryExpectation": "", "salaryCurrency": "USD",
  "willingToRelocate": false, "remotePreference": "remote|hybrid|onsite|any",
  "yearsExperience": "", "highestEducation": "",
  "gender": "Decline to answer", "race": "Decline to answer",
  "veteranStatus": "Decline to answer", "disabilityStatus": "Decline to answer",
  "customAnswers": [{ "question": "", "answer": "" }] }
```
Preflight required: firstName, lastName, phone, workAuthorizedCountries (non-empty), requiresSponsorship (boolean set).

## 7. Frontend
- `stores/apply.ts` — settings CRUD, `start(cardId)`, `getRun`, `control(runId, action)`, `input(runId, payload)`, `cardRuns(cardId)`, Gmail connect/disconnect.
- `components/JobCard.vue` — Apply button (wishlist only, `@click.stop`, `@mousedown.stop` to avoid drag), emits `apply`. Bubble through `KanbanColumn` (`card-apply`) → `KanbanBoard` → `PipelineView`.
- `components/ApplyLiveModal.vue` — starts or reattaches; polls `GET /apply/runs/:id` every 1.5 s; screenshot `<img>` with click → coords scaled to 1280×900; type box, Enter/Tab/Backspace/Esc buttons, scroll; status banner; review table of fields (label, value, source, low-confidence highlight); buttons by status: Take over / Resume agent / Submit / Mark applied / Cancel / Close. On `submitted` → `pipeline.fetchCards()`.
- `components/AutoApplySettings.vue` mounted in `ProfileView` — password (write-only), auto-submit toggle, cap (P2), Gmail connect/disconnect, LinkedIn/Indeed connect (P2), defaults form, custom Q&A list. Reads `?gmail=connected|error` to show a message.
- `components/ApplicationRecord.vue` in `JobDetailModal` — latest run summary + fields + screenshot link.

## 8. Env vars (`.env.example`)
```
CREDENTIALS_ENC_KEY=            # openssl rand -base64 32
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:3000/api/integrations/gmail/callback
APPLY_MAX_CONCURRENCY=2
APPLY_HEADLESS=true             # false to watch Chromium locally
```
HF Space secrets: same names. Google OAuth client: Web application, redirect URI = Space URL + `/api/integrations/gmail/callback`, Gmail API enabled, users added as test users.

## 9. Error handling & edge cases
- Agents unreachable at start → run `failed`, 502 to client with message.
- AI provider failure → fields left unanswered at confidence 0 → review (never blind submit).
- Posting closed (404 / "no longer accepting") → `failed` with message.
- "Already applied" text → `submitted` with message "Already applied".
- Card deleted mid-run → cascade deletes run row; tracker stops on missing row; agents run cancelled.
- Concurrent start from two tabs → unique active-run check in a transaction (`SELECT … FOR UPDATE` not needed; check-then-insert guarded by in-process lock per user).

## 10. Test plan
- Unit (python): `answers.rule_match` label → default mapping; option matching; `gate.decide` matrix; `gmail.extract_code_or_link` on sample bodies; `detect.resolve` URL patterns. Run `python3 -m pytest agents/apply/tests` (pytest added as optional dev dep) or plain asserts via `python3 -m agents.apply.selftest`.
- Gateway: `npm run build` compiles; manual curl of settings/start/status with JWT.
- Crypto round-trip + tamper detection.
- E2E manual: one live Greenhouse, Lever, Ashby posting with auto-submit OFF → verify review shows correct fields; cancel (do not submit to real employers during testing). Verify card move with `mark-applied`.
- Security review: grep logs/responses for secrets; confirm agents bound to 127.0.0.1.

## 11. Rollback / compatibility
- Schema is additive (`IF NOT EXISTS`); rollback = deploy previous image, tables unused.
- Feature is inert without `CREDENTIALS_ENC_KEY` (start preflight fails with a clear message).
- Binding agents to 127.0.0.1 is compatible: gateway already uses `http://localhost:8000`.
