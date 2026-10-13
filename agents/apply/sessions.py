"""Job-site sessions (LinkedIn, Dice): the user signs in once in the live view; we keep the cookies.

The agent never sees or stores the site password — only the resulting browser session, which the
gateway stores encrypted and hands back for later runs.
"""
import re
from urllib.parse import urlparse

from agents.apply.manager import Run, RunFailed

SITES: dict[str, dict] = {
    "linkedin": {
        "label": "LinkedIn",
        "login_url": "https://www.linkedin.com/login",
        "check_url": "https://www.linkedin.com/feed/",
        "domains": ("linkedin.com",),
    },
    "dice": {
        "label": "Dice",
        "login_url": "https://www.dice.com/dashboard/login",
        "check_url": "https://www.dice.com/dashboard/profiles",
        "domains": ("dice.com",),
    },
}

LOGIN_WALL_RE = re.compile(r"/login|/authwall|/checkpoint|/uas/|/signin|/sign-in|accounts\.google\.com", re.I)


def _on_site(url: str, site: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in SITES[site]["domains"])


def at_login_wall(url: str) -> bool:
    return bool(LOGIN_WALL_RE.search(url))


async def is_logged_in(run: Run, site: str) -> bool:
    """Open a members-only page; signed-in users stay there, others are sent to a login page."""
    page = run.page
    try:
        await page.goto(SITES[site]["check_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2500)
    except Exception:
        return False
    return _on_site(page.url, site) and not at_login_wall(page.url)


async def capture(run: Run, site: str) -> None:
    """Save the site's cookies / storage (refreshed after every run so sessions last longer)."""
    if not run.context:
        return
    state = await run.context.storage_state()
    domains = SITES[site]["domains"]

    def ours(host: str) -> bool:
        host = host.lstrip(".").lower()
        return any(host == d or host.endswith("." + d) for d in domains)

    run.session_updates[site] = {
        "cookies": [c for c in state.get("cookies", []) if ours(c.get("domain", ""))],
        "origins": [o for o in state.get("origins", []) if ours(urlparse(o.get("origin", "")).hostname or "")],
    }


async def _wait_for_sign_in(run: Run, site: str, message: str) -> None:
    """Pause until the user has signed in through the live view (verified, not just claimed)."""
    label = SITES[site]["label"]
    run.needs = {"kind": "signin", "site": site, "label": label}
    try:
        await _sign_in_loop(run, site, label, message)
    finally:
        run.needs = None


async def _sign_in_loop(run: Run, site: str, label: str, message: str) -> None:
    while True:
        await run.wait_for_user("needs_input", message)
        # Close leftover popups (e.g. "Sign in with Google") so the agent drives the main tab again.
        for p in list(run.context.pages if run.context else []):
            if p is not run.page and not p.is_closed():
                await p.close()
        if await is_logged_in(run, site):
            await capture(run, site)
            run.note(f"Signed in to {label}")
            return
        message = (f"Still not signed in to {label}. Use Take over to sign in on the page, "
                   f"then click “I'm signed in”.")
        await run.page.goto(SITES[site]["login_url"], wait_until="domcontentloaded", timeout=30000)


async def run_login(run: Run) -> None:
    """kind == "login": connect a site once from Profile."""
    site = run.login_site
    if site not in SITES:
        raise RunFailed(f"Unsupported site: {site}")
    label = SITES[site]["label"]
    run.site = site
    run.note(f"Opening the {label} sign-in page")
    if await is_logged_in(run, site):  # an earlier session still works
        await capture(run, site)
    else:
        await run.page.goto(SITES[site]["login_url"], wait_until="domcontentloaded", timeout=30000)
        await _wait_for_sign_in(
            run, site,
            f"Sign in to {label} in the live view: click Take over, sign in on the page with your {label} email "
            f"and password (complete any code or 2-step check), then click “I'm signed in”. "
            f"Avoid “Sign in with Google” — Google often blocks it in automated browsers.",
        )
    run.status, run.message = "submitted", f"{label} connected"


async def ensure_signed_in(run: Run, site: str, return_url: str) -> None:
    """Called by handlers when they hit a login wall: let the user sign in in place, then continue."""
    label = SITES[site]["label"]
    if not (run.req.get("sessions") or {}).get(site):
        hint = f"Connect {label} once in Profile → Auto-Apply to skip this next time. "
    else:
        hint = f"Your saved {label} session has expired. "
    await run.page.goto(SITES[site]["login_url"], wait_until="domcontentloaded", timeout=30000)
    await _wait_for_sign_in(
        run, site,
        f"{hint}Sign in to {label} in the live view (Take over), then click “I'm signed in”.",
    )
    await run.page.goto(return_url, wait_until="domcontentloaded", timeout=30000)
