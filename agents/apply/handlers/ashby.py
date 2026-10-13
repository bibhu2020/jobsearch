import re
from urllib.parse import urlparse

from agents.apply.handlers.base import SinglePageFormHandler


class AshbyHandler(SinglePageFormHandler):
    site = "ashby"
    submit_selectors = ['button[type="submit"]', 'button']
    submit_text = re.compile(r"submit application", re.I)

    def form_url(self, url: str) -> str:
        # jobs.ashbyhq.com/{company}/{job-id} → /{job-id}/application
        if urlparse(url).hostname != "jobs.ashbyhq.com":
            return url
        base = url.split("?")[0].rstrip("/")
        return base if base.endswith("/application") else f"{base}/application"
