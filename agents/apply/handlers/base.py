"""Shared application flow for single-page ATS forms (Greenhouse, Lever, Ashby…)."""
import asyncio
import re

from agents.apply import answers, detect, forms, gate
from agents.apply.manager import MarkedApplied, Run, RunFailed

MAX_FILL_PASSES = 3
MAX_SUBMIT_ATTEMPTS = 3
CONFIRM_WAIT_S = 30
APPLY_BUTTON_RE = re.compile(r"^\s*(apply|apply now|apply for this job|apply to this job|i'?m interested)\s*$", re.I)


def _plain(markdown_text: str) -> str:
    text = re.sub(r"^\s*(#+|---+)\s*", "", markdown_text or "", flags=re.M)
    return re.sub(r"\*\*|__|\*|`", "", text).strip()


def build_context(run: Run) -> dict:
    req = run.req
    applicant = req.get("applicant", {})
    job = req.get("job", {})
    files = req.get("files", {})
    return {
        "email": applicant.get("email"),
        "name": applicant.get("name"),
        "defaults": applicant.get("defaults") or {},
        "profile": applicant.get("profile") or {},
        "resume_text": applicant.get("resume_text", ""),
        "resume_filename": next(iter(run.files), None),
        "cover_letter_text": _plain(files.get("cover_letter_text", "")),
        "job_title": job.get("title"),
        "company": job.get("company"),
        "job_description": job.get("description"),
        "job_location": job.get("location") or "",
    }


class SinglePageFormHandler:
    site = "generic"
    confirmation_url_markers: tuple[str, ...] = ()
    submit_selectors = ['button[type="submit"]', 'input[type="submit"]']
    submit_text = re.compile(r"submit( application)?|send application|apply", re.I)
    root_selector: str | None = None   # limit form reading to this container (e.g. a modal dialog)

    def __init__(self, run: Run):
        self.run = run
        self.page = run.page
        self.ctx = build_context(run)
        self.auto_submit = bool(run.req.get("settings", {}).get("auto_submit", True))

    # ── Hooks for subclasses ────────────────────────────────────────────────
    def form_url(self, url: str) -> str:
        return url

    async def form_frame(self):
        return self.page.main_frame

    # ── Flow ────────────────────────────────────────────────────────────────
    async def run_flow(self) -> None:
        run = self.run
        run.site, run.channel = self.site, "ats"
        url = self.form_url(run.apply_url)
        run.apply_url = url
        run.note("Opening the application form")
        await self.goto(url)
        await self.follow_embedded_form()
        await self.ensure_open()
        await self.reveal_form()
        frame = await self.form_frame()

        await self.fill_all(frame)
        await self.review_gate(frame)
        await self.submit(frame)

    async def goto(self, url: str) -> None:
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            raise RunFailed(f"Could not open the job page ({type(e).__name__})")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

    async def body_text(self, frame=None) -> str:
        try:
            return await (frame or self.page.main_frame).inner_text("body", timeout=5000)
        except Exception:
            return ""

    async def follow_embedded_form(self) -> None:
        """Company career pages often embed the ATS form in an iframe — open it directly."""
        embedded = detect.embedded_form_url([f.url for f in self.page.frames[1:]])
        if embedded and embedded[0] == self.site:
            self.run.note("Opening the embedded application form")
            self.run.apply_url = embedded[1]
            await self.goto(embedded[1])

    async def ensure_open(self) -> None:
        text = await self.body_text()
        if detect.CLOSED_RE.search(text):
            raise RunFailed("This posting is no longer accepting applications")

    async def reveal_form(self) -> None:
        """Some boards show the description first and the form behind an Apply button."""
        frame = await self.form_frame()
        if len(await forms.extract(frame)) >= 3:
            return
        for loc in [self.page.get_by_role("button", name=APPLY_BUTTON_RE), self.page.get_by_role("link", name=APPLY_BUTTON_RE)]:
            if await loc.count():
                try:
                    await loc.first.click(timeout=5000)
                    await self.page.wait_for_timeout(1500)
                    return
                except Exception:
                    continue

    async def fill_all(self, frame) -> None:
        """Extract → answer → fill, repeated so conditional questions that appear get answered too."""
        known = {f["id"] for f in self.run.fields}
        for _ in range(MAX_FILL_PASSES):
            new = [f for f in await forms.extract(frame, self.root_selector) if f["id"] not in known]
            if not new:
                break
            self.run.note(f"Answering {len(new)} question(s)")
            await answers.answer_fields(new, self.ctx)
            for f in new:
                known.add(f["id"])
                self.run.fields.append(f)
                if not await forms.fill_field(frame, f, self.run.files):
                    f["confidence"] = 0
            await self.page.wait_for_timeout(500)
        await self.verify_values(frame)

    async def verify_values(self, frame) -> None:
        """Read back what the page actually holds; anything that didn't stick goes to review."""
        for f in self.run.fields:
            actual = await forms.read_value(frame, f)
            if actual is None:
                continue
            if f["type"] == "checkbox":
                f["value"] = bool(actual)
                continue
            if f["type"] == "file":
                if f.get("value") and not actual:
                    f["confidence"] = 0
                f["value"] = actual or ""
                continue
            if f.get("value") not in (None, "", []) and actual in ("", []):
                f["confidence"] = 0
            elif actual not in ("", []):
                f["value"] = actual  # the site may normalize what we typed

    async def sync_after_takeover(self, frame) -> None:
        """After the user worked in the page: their values win, and new questions get answered."""
        for f in self.run.fields:
            actual = await forms.read_value(frame, f)
            if actual not in (None, "", []) and actual != f.get("value"):
                f.update(value=actual, source="user", confidence=1.0)
        await self.fill_all(frame)

    async def check_done(self, frame) -> None:
        """If the user already submitted by hand, finish as applied."""
        if await self.is_confirmed(frame):
            self.run.status, self.run.message = "submitted", "Submitted by you"
            raise MarkedApplied()

    async def is_confirmed(self, frame) -> bool:
        text = await self.body_text()
        if frame is not self.page.main_frame:
            text += "\n" + await self.body_text(frame)
        if detect.ALREADY_APPLIED_RE.search(text):
            self.run.message = "Already applied to this job"
            return True
        return detect.is_confirmation(self.page.url, text, self.confirmation_url_markers)

    async def review_gate(self, frame) -> None:
        while True:
            captcha = await detect.visible_captcha(self.page)
            ok, reasons = gate.decide(self.run.fields, self.auto_submit, captcha, await forms.form_errors(frame, self.root_selector))
            if ok:
                self.run.auto_submitted = True
                return
            summary = "; ".join(reasons[:4]) + (f" (+{len(reasons) - 4} more)" if len(reasons) > 4 else "")
            action = await self.run.wait_for_user("awaiting_review", f"Review needed — {summary}")
            await self.check_done(frame)
            await self.sync_after_takeover(frame)
            if action == "submit":
                self.run.auto_submitted = False
                return

    async def click_submit(self, frame) -> None:
        for sel in self.submit_selectors:
            loc = frame.locator(sel).filter(has_text=self.submit_text) if "button" in sel else frame.locator(sel)
            for i in range(await loc.count()):
                el = loc.nth(i)
                if await el.is_visible():
                    await el.scroll_into_view_if_needed(timeout=5000)
                    await el.click(timeout=10000)
                    return
        btn = frame.get_by_role("button", name=self.submit_text)
        if await btn.count():
            await btn.last.click(timeout=10000)
            return
        raise RunFailed("Could not find the submit button")

    async def submit(self, frame) -> None:
        run = self.run
        for attempt in range(1, MAX_SUBMIT_ATTEMPTS + 1):
            run.status = "submitting"
            run.note("Submitting the application" + (f" (attempt {attempt})" if attempt > 1 else ""))
            await self.click_submit(frame)

            for _ in range(CONFIRM_WAIT_S):
                await asyncio.sleep(1)
                if await self.is_confirmed(frame):
                    run.status = "submitted"
                    run.message = run.message or ("Submitted automatically" if run.auto_submitted else "Submitted after your review")
                    run.note("Application submitted")
                    return
                if await detect.visible_captcha(self.page):
                    await run.wait_for_user("needs_input", "Solve the CAPTCHA in the live view, then click Resume agent")
                    await self.check_done(frame)
                    break  # re-click submit
            else:
                errors = await forms.form_errors(frame, self.root_selector)
                if not errors:
                    raise RunFailed("Submitted, but no confirmation was detected — please check the job site")
                await run.wait_for_user("awaiting_review", "The site reported problems: " + "; ".join(errors[:3]))
                await self.check_done(frame)
                await self.sync_after_takeover(frame)
        raise RunFailed("Could not submit after several attempts")
