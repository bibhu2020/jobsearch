"""LinkedIn: Easy Apply in the modal wizard, or follow "Apply" to the employer's own site."""
import re

from agents.apply import sessions
from agents.apply.handlers.multistep import StepFormHandler
from agents.apply.manager import MarkedApplied, RunFailed

APPLY_BUTTON = "button.jobs-apply-button, .jobs-apply-button--top-card button, .jobs-s-apply button"
CLOSED_RE = re.compile(r"no longer accepting applications", re.I)
APPLIED_RE = re.compile(r"\bApplied\s+\d+\s+(second|minute|hour|day|week|month)s?\s+ago|application (was )?submitted", re.I)


def canonical_job_url(url: str) -> str:
    m = re.search(r"currentJobId=(\d+)", url) or re.search(r"/jobs/view/(?:[^/?]*?-)?(\d{6,})", url)
    return f"https://www.linkedin.com/jobs/view/{m.group(1)}/" if m else url


class LinkedInHandler(StepFormHandler):
    site = "linkedin"
    root_selector = ".jobs-easy-apply-modal, div[role='dialog']"
    next_re = re.compile(r"^\s*(next|continue|review|continue to next step|review your application)\s*$", re.I)
    final_re = re.compile(r"^\s*submit( application)?\s*$", re.I)

    async def resolve(self, url: str) -> str | None:
        """Applies via Easy Apply and returns None, or returns the employer URL to continue with."""
        run, page = self.run, self.page
        run.site = "linkedin"
        job_url = canonical_job_url(url)
        run.apply_url = job_url
        run.note("Opening the LinkedIn job")
        await self.goto(job_url)
        no_button = await page.locator(APPLY_BUTTON).count() == 0
        sign_in_link = await page.get_by_role("link", name=re.compile(r"^sign in$", re.I)).count()
        if sessions.at_login_wall(page.url) or (no_button and sign_in_link):
            await sessions.ensure_signed_in(run, "linkedin", job_url)
            await page.wait_for_timeout(2500)

        text = await self.body_text()
        if CLOSED_RE.search(text):
            raise RunFailed("This LinkedIn job is no longer accepting applications")
        if APPLIED_RE.search(text):
            run.status, run.message = "submitted", "Already applied on LinkedIn"
            raise MarkedApplied()

        button = page.locator(APPLY_BUTTON).first
        if not await button.count():
            await run.wait_for_user(
                "needs_input",
                "Couldn't find LinkedIn's Apply button — take over to apply, then click Mark applied.",
            )
            raise RunFailed("LinkedIn Apply button not found")
        label = (await button.inner_text()).strip().lower()

        if "easy apply" in label:
            await self.easy_apply(button)
            await sessions.capture(run, "linkedin")
            return None
        return await self.external_url(button)

    async def easy_apply(self, button) -> None:
        run = self.run
        allowance = run.req.get("easy_apply") or {}
        if not allowance.get("allowed", False):
            raise RunFailed(allowance.get("reason") or "Easy Apply limit reached for today")
        run.channel = "easy_apply"
        run.note("Starting LinkedIn Easy Apply")
        await button.click(timeout=10000)
        try:
            await self.page.wait_for_selector(self.root_selector, timeout=15000)
        except Exception:
            raise RunFailed("LinkedIn's Easy Apply window didn't open")
        await self.step_loop(self.page.main_frame)

    async def external_url(self, button) -> str:
        """LinkedIn's "Apply" opens the employer site in a new tab (sometimes after a Continue dialog)."""
        run, page = self.run, self.page
        run.note("Following LinkedIn's Apply link to the employer's site")
        for attempt in range(2):
            try:
                async with page.context.expect_page(timeout=12000) as new_tab:
                    if attempt == 0:
                        await button.click(timeout=10000)
                    else:
                        cont = page.get_by_role("button", name=re.compile(r"^\s*continue\s*$", re.I))
                        if not await cont.count():
                            break
                        await cont.first.click(timeout=10000)
                tab = await new_tab.value
                await tab.wait_for_load_state("domcontentloaded", timeout=30000)
                url = tab.url
                await tab.close()
                if url and "linkedin.com" not in url:
                    return url
            except Exception:
                if "linkedin.com" not in page.url:  # navigated in the same tab
                    return page.url
        raise RunFailed("Couldn't open the employer's application page from LinkedIn")

