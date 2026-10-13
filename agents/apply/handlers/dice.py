"""Dice: its own multi-step application (needs a Dice session), or an external employer link."""
import re
from urllib.parse import urlparse

from agents.apply import sessions
from agents.apply.handlers.multistep import StepFormHandler
from agents.apply.manager import MarkedApplied, RunFailed

CLOSED_RE = re.compile(r"no longer available|job (has )?expired|this job is closed|position (has been )?filled", re.I)
APPLIED_RE = re.compile(r"you('ve| have) (already )?applied|application (was )?submitted|applied on \w+", re.I)


def job_id(url: str) -> str | None:
    m = re.search(r"/job-detail/([0-9a-f-]{36})", url) or re.search(r"/job-applications/([0-9a-f-]{36})", url)
    return m.group(1) if m else None


class DiceHandler(StepFormHandler):
    site = "dice"
    root_selector = None  # Dice's application is a full page
    next_re = re.compile(r"^\s*(next|continue|save and continue|review)\s*$", re.I)
    final_re = re.compile(r"^\s*(submit|submit application|apply)\s*$", re.I)
    confirmation_url_markers = ("/application-submitted", "/success")

    async def resolve(self, url: str) -> str | None:
        """Applies on Dice and returns None, or returns the employer URL to continue with."""
        run, page = self.run, self.page
        run.site = "dice"
        jid = job_id(url)
        if not jid:
            raise RunFailed("Unrecognized Dice job link")
        detail = f"https://www.dice.com/job-detail/{jid}"
        run.apply_url = detail
        run.note("Opening the Dice job")
        await self.goto(detail)
        text = await self.body_text()
        if CLOSED_RE.search(text):
            raise RunFailed("This Dice job is no longer available")

        start = f"https://www.dice.com/job-applications/{jid}/start-apply"
        await self.goto(start)
        if sessions.at_login_wall(page.url):
            await sessions.ensure_signed_in(run, "dice", start)
            await page.wait_for_timeout(2500)
        if sessions.at_login_wall(page.url):
            raise RunFailed("Not signed in to Dice")

        host = (urlparse(page.url).hostname or "").lower()
        if not host.endswith("dice.com"):
            return page.url  # Dice sent us to the employer's own application

        text = await self.body_text()
        if APPLIED_RE.search(text):
            run.status, run.message = "submitted", "Already applied on Dice"
            raise MarkedApplied()

        allowance = run.req.get("easy_apply") or {}
        if not allowance.get("allowed", False):
            raise RunFailed(allowance.get("reason") or "Daily limit for LinkedIn/Dice applications reached")
        run.channel = "easy_apply"
        run.apply_url = page.url
        run.note("Filling Dice's application")
        await self.step_loop(page.main_frame)
        await sessions.capture(run, "dice")
