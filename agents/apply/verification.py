"""Email verification: read the code/link from Gmail, or ask the user to type it."""
from urllib.parse import urlparse

from agents.apply import gmail
from agents.apply.manager import Run


def _as_result(value: str) -> dict:
    value = value.strip()
    if urlparse(value).scheme in ("http", "https"):
        return {"link": value}
    return {"code": value}


async def obtain_verification(run: Run, sender_domain: str, site_label: str = "The job site") -> dict:
    """Returns {"code": ...} or {"link": ...}, or {"manual": True} when the user completed it in the live view."""
    refresh_token = (run.req.get("gmail") or {}).get("refresh_token")
    if refresh_token:
        run.note("Checking Gmail for the verification email")
        try:
            found = await gmail.wait_for_verification(refresh_token, sender_domain, run.started_epoch)
            if found:
                run.note("Found the verification email")
                return found
            run.note("No verification email arrived in Gmail")
        except gmail.GmailAuthError:
            run.gmail_invalid = True
            run.note("Gmail access has expired — reconnect it in Profile")
        except Exception as err:
            run.note(f"Could not read Gmail ({type(err).__name__})")

    email = (run.req.get("applicant") or {}).get("email", "your email")
    run.needs = {"kind": "verification", "email": email, "sender": sender_domain}
    run.provided = None
    try:
        await run.wait_for_user(
            "needs_input",
            f"{site_label} sent a verification email to {email}. Type the code or paste the link below "
            "(or finish it yourself with Take over, then click Resume agent).",
        )
        value, run.provided = run.provided, None
        return _as_result(value) if value and value.strip() else {"manual": True}
    finally:
        run.needs = None
