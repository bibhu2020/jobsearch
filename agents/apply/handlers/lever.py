import re

from agents.apply.handlers.base import SinglePageFormHandler


class LeverHandler(SinglePageFormHandler):
    site = "lever"
    confirmation_url_markers = ("/thanks",)
    submit_selectors = ['#btn-submit', 'button[type="submit"]']
    submit_text = re.compile(r"submit( application)?", re.I)

    def form_url(self, url: str) -> str:
        # jobs.lever.co/{company}/{posting-id} → /{posting-id}/apply
        base = url.split("?")[0].rstrip("/")
        return base if base.endswith("/apply") else f"{base}/apply"
