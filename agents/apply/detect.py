"""URL / page classification: which handler applies, CAPTCHA and confirmation detection."""
import re
from urllib.parse import urlparse, parse_qs

CONFIRMATION_RE = re.compile(
    r"thank(s| you)[^.]{0,40}\b(for )?(applying|your application|submitting|your interest)"
    r"|application (has been |was )?(submitted|received)"
    r"|we('ve| have) received your application",
    re.I,
)
ALREADY_APPLIED_RE = re.compile(r"(you('ve| have)|already) (already )?applied", re.I)
CLOSED_RE = re.compile(
    r"no longer (accepting applications|available|open)|position (has been )?(filled|closed)"
    r"|job (is )?(no longer|not) (available|found)|this job has expired",
    re.I,
)
CAPTCHA_FRAME_RE = re.compile(r"recaptcha/(api2|enterprise)/bframe|hcaptcha\.com/captcha|challenges\.cloudflare\.com", re.I)


def site_for_url(url: str) -> str | None:
    """Classify a URL by the application platform it belongs to."""
    host = (urlparse(url).hostname or "").lower()
    qs = parse_qs(urlparse(url).query)
    if host.endswith("greenhouse.io") or "gh_jid" in qs:
        return "greenhouse"
    if host == "jobs.lever.co":
        return "lever"
    if host == "jobs.ashbyhq.com" or "ashby_jid" in qs:
        return "ashby"
    if host.endswith("linkedin.com"):
        return "linkedin"
    if host.endswith("indeed.com"):
        return "indeed"
    if "myworkdayjobs.com" in host or "myworkdaysite.com" in host:
        return "workday"
    if "icims.com" in host:
        return "icims"
    if "taleo.net" in host:
        return "taleo"
    return None


def embedded_form_url(frame_urls: list[str]) -> tuple[str, str] | None:
    """A company careers page that embeds a Greenhouse / Ashby / Lever form → (site, direct form URL)."""
    for src in frame_urls:
        host = (urlparse(src).hostname or "").lower()
        if host.endswith("greenhouse.io") and ("embed/job_app" in src or "/jobs/" in src):
            return "greenhouse", src
        if host == "jobs.ashbyhq.com":
            return "ashby", src.replace("/embed", "")
        if host == "jobs.lever.co":
            return "lever", src
    return None


def is_confirmation(url: str, text: str, url_markers: tuple[str, ...] = ()) -> bool:
    if any(m in url for m in url_markers):
        return True
    return bool(CONFIRMATION_RE.search(text or ""))


async def visible_captcha(page) -> bool:
    """True when a CAPTCHA challenge (not just the invisible badge) is on screen."""
    for frame in page.frames:
        if not CAPTCHA_FRAME_RE.search(frame.url or ""):
            continue
        try:
            el = await frame.frame_element()
            box = await el.bounding_box()
            if box and box["width"] > 50 and box["height"] > 50 and await el.is_visible():
                return True
        except Exception:
            continue
    return False
