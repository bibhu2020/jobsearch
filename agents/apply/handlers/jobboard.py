"""Job boards (remote100k and others) only list jobs: find their "Apply" link to the employer's site."""
import re
from urllib.parse import urlparse

from agents.apply import detect

APPLY_LINK_RE = re.compile(
    r"^\s*(apply( now)?|apply (for|to) (this|the) (job|position|role)|apply on (the )?company('s)? (site|website)"
    r"|apply externally|view (and|&) apply)\s*$",
    re.I,
)
# Upsells / navigation that look like apply links but aren't
NOT_APPLY_RE = re.compile(r"auto[- ]?apply|copilot|sign ?up|log ?in|#", re.I)

LINKS_JS = r"""
() => [...document.querySelectorAll('a[href]')].map(a => ({
  text: (a.innerText || a.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 80),
  href: a.href,
}))
"""


def pick_apply_link(links: list[dict], page_url: str) -> str | None:
    """Best external apply link: prefer ones that point at an ATS we can automate."""
    own = (urlparse(page_url).hostname or "").lower().removeprefix("www.")
    candidates = []
    for link in links:
        href, text = link.get("href") or "", link.get("text") or ""
        host = (urlparse(href).hostname or "").lower().removeprefix("www.")
        if not host or host == own or not href.startswith("http"):
            continue
        if not APPLY_LINK_RE.search(text) or NOT_APPLY_RE.search(text) or NOT_APPLY_RE.search(href.split("?")[0]):
            continue
        candidates.append(href)
    if not candidates:
        return None
    fillable = [h for h in candidates if detect.site_for_url(h) in ("greenhouse", "lever", "ashby")]
    known = [h for h in candidates if detect.site_for_url(h)]
    return (fillable or known or candidates)[0]


async def find_apply_link(page) -> str | None:
    try:
        links = await page.evaluate(LINKS_JS)
    except Exception:
        return None
    return pick_apply_link(links, page.url)
