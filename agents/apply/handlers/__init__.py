"""Picks the handler for a job URL and runs it."""
from agents.apply import detect
from agents.apply.handlers.ashby import AshbyHandler
from agents.apply.handlers.greenhouse import GreenhouseHandler
from agents.apply.handlers.lever import LeverHandler
from agents.apply.manager import Run, RunFailed

HANDLERS = {
    "greenhouse": GreenhouseHandler,
    "lever": LeverHandler,
    "ashby": AshbyHandler,
}

SITE_NAMES = {
    "linkedin": "LinkedIn Easy Apply", "indeed": "Indeed", "workday": "Workday",
    "icims": "iCIMS", "taleo": "Taleo", None: "This job site",
}


async def run_apply(run: Run) -> None:
    if run.kind != "apply":
        raise RunFailed(f"Unsupported run kind: {run.kind}")
    url = run.apply_url
    if not url:
        raise RunFailed("This job has no posting URL")

    site = detect.site_for_url(url)
    if site not in HANDLERS:
        # A company careers page may embed a supported ATS form.
        run.note("Looking for the application form")
        try:
            await run.page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await run.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        embedded = detect.embedded_form_url([f.url for f in run.page.frames[1:]])
        if embedded:
            site, run.apply_url = embedded

    handler_cls = HANDLERS.get(site)
    if handler_cls:
        await handler_cls(run).run_flow()
        return

    # Not automated yet: the user can apply through the live view and confirm.
    run.site = site or "generic"
    if run.page.url in ("about:blank", ""):
        await run.page.goto(url, wait_until="domcontentloaded", timeout=45000)
    while True:
        await run.wait_for_user(
            "needs_input",
            f"{SITE_NAMES.get(site, 'This job site')} isn't automated yet — take over to apply in the live view, "
            "then click Mark applied.",
        )
