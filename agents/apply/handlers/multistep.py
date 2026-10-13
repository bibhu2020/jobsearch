"""Multi-step application wizards (LinkedIn Easy Apply, Dice): fill a step → Next → … → Submit."""
import asyncio
import hashlib
import re

from agents.apply import detect, forms
from agents.apply.handlers.base import SinglePageFormHandler
from agents.apply.manager import RunFailed

MAX_STEPS = 15
STUCK_LIMIT = 2


class StepFormHandler(SinglePageFormHandler):
    """Subclasses set `root_selector` (the wizard container) and may tune the button patterns."""
    next_re = re.compile(r"^\s*(next|continue|review|review your application|continue to next step|save and continue)\s*$", re.I)
    final_re = re.compile(r"^\s*(submit|submit application|send application|apply|finish)\s*$", re.I)

    def scope(self, frame):
        return frame.locator(self.root_selector).first if self.root_selector else frame

    async def find_button(self, frame, pattern: re.Pattern):
        """Last visible, enabled button in the wizard whose accessible name matches."""
        buttons = self.scope(frame).get_by_role("button", name=pattern)
        for i in reversed(range(await buttons.count())):
            btn = buttons.nth(i)
            try:
                if await btn.is_visible() and await btn.is_enabled():
                    return btn
            except Exception:
                continue
        return None

    async def step_signature(self, frame) -> str:
        """Fingerprint of the current step, to notice when Next didn't advance."""
        try:
            text = await self.scope(frame).inner_text(timeout=3000)
        except Exception:
            text = ""
        return hashlib.sha1(text.encode()).hexdigest()

    async def click_submit(self, frame) -> None:
        btn = await self.find_button(frame, self.final_re)
        if not btn:
            raise RunFailed("Could not find the submit button")
        await btn.click(timeout=10000)

    async def step_loop(self, frame) -> None:
        run = self.run
        stuck = 0
        for step in range(1, MAX_STEPS + 1):
            run.note(f"Step {step}")
            await self.fill_all(frame)

            if await self.find_button(frame, self.final_re):
                await self.review_gate(frame)
                await self.submit(frame)
                return

            next_btn = await self.find_button(frame, self.next_re)
            if not next_btn:
                if await self.is_confirmed(frame):
                    run.status = "submitted"
                    return
                await run.wait_for_user(
                    "awaiting_review",
                    "Couldn't find the next step — take over to continue, then click Resume agent.",
                )
                await self.check_done(frame)
                await self.sync_after_takeover(frame)
                continue

            before = await self.step_signature(frame)
            await next_btn.click(timeout=10000)
            await asyncio.sleep(1.5)
            if await self.step_signature(frame) != before:
                stuck = 0
                continue

            # Didn't advance: usually a required question we couldn't answer.
            stuck += 1
            await self.fill_all(frame)
            if stuck >= STUCK_LIMIT:
                errors = await forms.form_errors(frame, self.root_selector)
                detail = "; ".join(errors[:3]) or "a question needs an answer"
                await run.wait_for_user(
                    "awaiting_review",
                    f"Stuck on this step ({detail}) — take over to fix it, then click Resume agent.",
                )
                await self.check_done(frame)
                await self.sync_after_takeover(frame)
                stuck = 0
        raise RunFailed("The application had more steps than expected — please finish it in the live view")

    async def is_confirmed(self, frame) -> bool:
        if await super().is_confirmed(frame):
            return True
        # Wizards often confirm inside the dialog only
        try:
            text = await self.scope(frame).inner_text(timeout=2000)
        except Exception:
            return False
        return bool(detect.CONFIRMATION_RE.search(text))
