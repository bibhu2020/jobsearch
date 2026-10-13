"""Picks the handler for a job URL and runs it.

Job boards and LinkedIn/Dice often just point at the employer's own application, so dispatch follows
up to MAX_HOPS redirections ("Apply" links) until it reaches a form we can fill.
"""
from urllib.parse import urlparse

from agents.apply import detect, sessions
from agents.apply.handlers import jobboard
from agents.apply.handlers.ashby import AshbyHandler
from agents.apply.handlers.dice import DiceHandler
from agents.apply.handlers.greenhouse import GreenhouseHandler
from agents.apply.handlers.lever import LeverHandler
from agents.apply.handlers.linkedin import LinkedInHandler
from agents.apply.manager import Run, RunFailed

MAX_HOPS = 3

# Sites whose application form we fill directly
FORM_HANDLERS = {
    "greenhouse": GreenhouseHandler,
    "lever": LeverHandler,
    "ashby": AshbyHandler,
}
# Sites that either apply in their own wizard or hand us the employer's URL
RESOLVING_HANDLERS = {
    "linkedin": LinkedInHandler,
    "dice": DiceHandler,
}

SITE_NAMES = {
    "indeed": "Indeed", "workday": "Workday", "icims": "iCIMS", "taleo": "Taleo",
}


async def _open(run: Run, url: str) -> None:
    try:
        await run.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await run.page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass


async def run_apply(run: Run) -> None:
    if run.kind == "login":
        await sessions.run_login(run)
        return
    if run.kind != "apply":
        raise RunFailed(f"Unsupported run kind: {run.kind}")
    url = run.apply_url
    if not url:
        raise RunFailed("This job has no posting URL")

    for _ in range(MAX_HOPS + 1):
        site = detect.site_for_url(url)
        run.apply_url = url

        if site in FORM_HANDLERS:
            await FORM_HANDLERS[site](run).run_flow()
            return

        if site in RESOLVING_HANDLERS:
            next_url = await RESOLVING_HANDLERS[site](run).resolve(url)
            if next_url is None:
                return  # applied in the site's own wizard
            run.note(f"Continuing on {urlparse(next_url).hostname}")
            url = next_url
            continue

        if site in SITE_NAMES:
            break  # known ATS we can't automate yet

        # Job board / company careers page: embedded form, or an "Apply" link to follow.
        run.note("Looking for the application form")
        await _open(run, url)
        text = await run.page.inner_text("body") if not run.page.is_closed() else ""
        if detect.CLOSED_RE.search(text):
            raise RunFailed("This posting is no longer accepting applications")
        embedded = detect.embedded_form_url([f.url for f in run.page.frames[1:]])
        if embedded:
            url = embedded[1]
            continue
        link = await jobboard.find_apply_link(run.page)
        if link and link != url:
            run.note(f"Following the apply link to {urlparse(link).hostname}")
            url = link
            continue
        break

    # Not automated: the user applies through the live view and confirms.
    site = detect.site_for_url(url)
    run.site = site or "generic"
    if run.page.url in ("about:blank", "") or run.page.url.split("#")[0] != url.split("#")[0]:
        await _open(run, url)
    name = SITE_NAMES.get(site or "", f"This job site ({urlparse(url).hostname})")
    while True:
        await run.wait_for_user(
            "needs_input",
            f"{name} isn't automated yet — take over to apply in the live view, then click Mark applied.",
        )
