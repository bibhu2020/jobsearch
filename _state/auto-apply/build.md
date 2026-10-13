# Build — Auto-Apply

## Phase 1 status: implemented (2026-10-13)

| Area | Files |
|---|---|
| Schema | `shared/schema.pg.sql`, `shared/init.sql` — `user_apply_settings`, `user_site_sessions`, `ats_accounts`, `application_runs` |
| Gateway | `crypto/` (AES-256-GCM), `apply/` (settings, start/status/input/control, background tracker), `integrations/` (Gmail OAuth) |
| Agents | `agents/apply/` — `manager.py`, `forms.py`, `answers.py`, `gate.py`, `detect.py`, `gmail.py`, `handlers/{greenhouse,lever,ashby}.py`, `router.py`, `selftest.py` |
| Frontend | `stores/apply.ts`, `ApplyLiveModal.vue`, `AutoApplySettings.vue` (Profile), `ApplicationRecord.vue` (job detail), Apply button on Wishlist `JobCard` |
| Privacy | Confirmation screenshots stored in Postgres and served only to their owner — the GitHub artifacts repo is public |
| Multi-user | Per-user daily cap, global pending-run cap, global Easy Apply cap, queue position; typed-code verification fallback; Gmail expiry auto-disconnect; graceful handling of a changed encryption key |
| Deploy | agents bound to `127.0.0.1` in `supervisord.conf`; service worker no longer serves `index.html` for `/api/*` navigations (OAuth callback) |

## Validation
- `PYTHONPATH=. python3 -m agents.apply.selftest` — rules, option matching, gate, URL detection, Gmail parsing: pass.
- `npm run build` (gateway + frontend, vue-tsc): pass.
- Local fake ATS form (scratch HTTP server) + throwaway Postgres container, through gateway → agents:
  - preflight returns the missing-setup list; password stored as `v1:` ciphertext, never returned;
  - second start returns the active run; `submit` rejected while `needs_input`;
  - unsupported site → `needs_input` → `mark-applied` → card moved to Applied;
  - Greenhouse-classified form → auto-submitted, 9 answers recorded, confirmation screenshot stored, card moved to Applied;
  - auto-submit off → `awaiting_review` → `submit` → submitted with `auto_submitted = false`;
  - AI providers down → optional question left blank (no invented answer).
- Multi-user (throwaway Postgres, limits lowered via env): 2nd user refused with 429 while 1 run pending (max 1);
  3rd run of the day refused with 429 (limit 2) while another user still starts; queued run shows "you're next" and
  starts when the slot frees; verification input refused unless the run asks for it; after changing
  `CREDENTIALS_ENC_KEY`, start returns "re-enter your password" (not a 500) and works once re-entered.
- Self-tests cover the verification fallback: Gmail hit, no Gmail → typed code, expired Gmail → flagged + pasted link, manual completion.
- Not yet validated: live Greenhouse / Lever / Ashby postings (do with auto-submit OFF and cancel), real Gmail OAuth round-trip, CAPTCHA hand-off.

## Next phases
**Prerequisite for P3 (deferred by product owner, 2026-10-13):** signup does not verify that the user owns their email.
P3 creates job-site accounts with the login email, so add email verification at signup (or require the connected
Gmail address to match the login email) before enabling account creation.

P2 LinkedIn/Indeed (sessions, Easy Apply, cap UI), P3 account sites (Workday, iCIMS/Taleo + Gmail verification), P4 generic LLM handler.
