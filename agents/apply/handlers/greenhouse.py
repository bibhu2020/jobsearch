import re

from agents.apply.handlers.base import SinglePageFormHandler


class GreenhouseHandler(SinglePageFormHandler):
    site = "greenhouse"
    confirmation_url_markers = ("/confirmation",)
    submit_selectors = ['#submit_app', 'button[type="submit"]', 'input[type="submit"]']
    submit_text = re.compile(r"submit( application)?", re.I)
