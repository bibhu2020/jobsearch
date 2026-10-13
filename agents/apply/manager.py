"""In-memory run registry: one Playwright browser per application run."""
import asyncio
import base64
import os
import shutil
import tempfile
import time
from datetime import datetime

from playwright.async_api import async_playwright

MAX_CONCURRENCY = int(os.getenv("APPLY_MAX_CONCURRENCY", "2"))
HEADLESS = os.getenv("APPLY_HEADLESS", "true").lower() != "false"
VIEWPORT = {"width": 1280, "height": 900}
USER_IDLE_TIMEOUT_S = 10 * 60
KEEP_FINISHED_S = 15 * 60
TERMINAL = {"submitted", "failed", "cancelled"}

# Which control actions are accepted in which status
ALLOWED_ACTIONS = {
    "resume": {"needs_input", "awaiting_review"},
    "submit": {"awaiting_review"},
    "mark-applied": {"needs_input", "awaiting_review"},
    "finish-login": {"needs_input"},
}


class RunFailed(Exception):
    """Ends the run as `failed` with a user-facing message."""


class RunCancelled(Exception):
    """Ends the run as `cancelled`."""


class MarkedApplied(Exception):
    """The user applied by hand (take-over) and confirmed it."""


class Run:
    def __init__(self, req: dict):
        self.req = req
        self.id: str = req["run_id"]
        self.kind: str = req.get("kind", "apply")
        self.status = "queued"
        self.site: str | None = None
        self.channel: str | None = None
        self.apply_url: str | None = req.get("job", {}).get("url")
        self.message = "Waiting for a free browser slot"
        self.step = ""
        self.log: list[str] = []
        self.fields: list[dict] = []
        self.auto_submitted = False
        self.new_accounts: list[str] = []
        self.session_updates: dict = {}
        self.screenshot: bytes | None = None
        self.page = None
        self.task: asyncio.Task | None = None
        self.actions: asyncio.Queue[str] = asyncio.Queue()
        self.started_epoch = time.time()
        self.finished_at: float | None = None
        self.workdir = tempfile.mkdtemp(prefix="ll-apply-")
        self.files: dict[str, str] = {}
        self.stop_shots = False
        self.needs: dict | None = None          # e.g. {"kind": "verification", "email": ...}
        self.provided: str | None = None        # value typed by the user for `needs`
        self.gmail_invalid = False              # tell the gateway to clear the stored Gmail token

    def note(self, msg: str) -> None:
        self.step = msg
        self.log.append(f"{datetime.now():%H:%M:%S} {msg}")
        del self.log[:-60]

    async def wait_for_user(self, status: str, message: str) -> str:
        """Pause in `status` until the user sends a control action; returns it."""
        self.status, self.message = status, message
        self.note(message)
        while not self.actions.empty():
            self.actions.get_nowait()
        try:
            action = await asyncio.wait_for(self.actions.get(), USER_IDLE_TIMEOUT_S)
        except asyncio.TimeoutError:
            raise RunCancelled("Cancelled after 10 minutes without a response")
        if action == "mark-applied":
            raise MarkedApplied()
        self.status, self.message = "running", ""
        return action

    def snapshot(self, include_screenshot: bool = True) -> dict:
        public_fields = [
            {k: f.get(k) for k in ("id", "label", "type", "required", "value", "source", "confidence", "sensitive", "options")}
            for f in self.fields
        ]
        return {
            "id": self.id,
            "kind": self.kind,
            "status": self.status,
            "site": self.site,
            "channel": self.channel,
            "apply_url": self.apply_url,
            "auto_submitted": self.auto_submitted,
            "message": self.message,
            "step": self.step,
            "log": self.log[-30:],
            "fields": public_fields,
            "new_accounts": self.new_accounts,
            "session_updates": self.session_updates,
            "needs": self.needs,
            "gmail_invalid": self.gmail_invalid,
            "screenshot": base64.b64encode(self.screenshot).decode() if include_screenshot and self.screenshot else None,
        }


class RunManager:
    def __init__(self):
        self.runs: dict[str, Run] = {}
        self.slots = asyncio.Semaphore(MAX_CONCURRENCY)

    def prune(self) -> None:
        now = time.time()
        for rid in [r.id for r in self.runs.values() if r.finished_at and now - r.finished_at > KEEP_FINISHED_S]:
            del self.runs[rid]

    def get(self, run_id: str) -> Run | None:
        self.prune()
        return self.runs.get(run_id)

    def start(self, req: dict) -> Run:
        self.prune()
        existing = self.runs.get(req["run_id"])
        if existing:
            return existing
        run = Run(req)
        self.runs[run.id] = run
        run.task = asyncio.create_task(self._execute(run))
        return run

    def cancel(self, run: Run) -> None:
        if run.status in TERMINAL:
            return
        if run.task and not run.task.done():
            run.task.cancel()

    async def _screenshot_loop(self, run: Run) -> None:
        while not run.stop_shots:
            try:
                if run.page and not run.page.is_closed():
                    run.screenshot = await run.page.screenshot(type="jpeg", quality=55, timeout=5000)
            except Exception:
                pass
            await asyncio.sleep(1)

    async def _execute(self, run: Run) -> None:
        from agents.apply.handlers import run_apply  # late import: handlers import manager

        shots: asyncio.Task | None = None
        try:
            async with self.slots:
                run.status, run.message = "running", ""
                run.note("Starting browser")
                self._write_files(run)
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=HEADLESS)
                    try:
                        context = await browser.new_context(viewport=VIEWPORT, locale="en-US")
                        run.page = await context.new_page()
                        shots = asyncio.create_task(self._screenshot_loop(run))
                        await run_apply(run)
                    finally:
                        if shots:
                            # Let an in-flight screenshot finish before the browser closes.
                            run.stop_shots = True
                            try:
                                await asyncio.wait_for(shots, 7)
                            except (asyncio.TimeoutError, asyncio.CancelledError):
                                pass
                        try:
                            if run.page and not run.page.is_closed():
                                run.screenshot = await run.page.screenshot(type="jpeg", quality=70, timeout=5000)
                        except Exception:
                            pass
                        await browser.close()
        except MarkedApplied:
            if run.status != "submitted":
                run.message = "Marked as applied by you"
            run.status, run.auto_submitted = "submitted", False
        except RunCancelled as e:
            run.status, run.message = "cancelled", str(e) or "Cancelled"
        except asyncio.CancelledError:
            run.status, run.message = "cancelled", "Cancelled by you"
        except RunFailed as e:
            run.status, run.message = "failed", str(e)
        except Exception as e:  # unexpected — keep the message short, never include secrets
            print(f"apply: run {run.id} crashed: {type(e).__name__}: {e}")
            run.status, run.message = "failed", f"Unexpected error: {type(e).__name__}"
        finally:
            if run.status not in TERMINAL:
                run.status, run.message = "failed", run.message or "Run ended unexpectedly"
            run.note(f"Finished: {run.status}{' — ' + run.message if run.message else ''}")
            run.finished_at = time.time()
            run.page = None
            run.req = {}  # drop secrets as soon as the run ends
            shutil.rmtree(run.workdir, ignore_errors=True)

    @staticmethod
    def _write_files(run: Run) -> None:
        resume = (run.req.get("files") or {}).get("resume")
        if resume and resume.get("b64"):
            name = os.path.basename(resume.get("filename") or "Resume.pdf")
            path = os.path.join(run.workdir, name)
            with open(path, "wb") as fh:
                fh.write(base64.b64decode(resume["b64"]))
            run.files[name] = path


manager = RunManager()
