"""Auto-submit decision (PRD FR-10)."""

CONFIDENCE_THRESHOLD = 0.8


def decide(fields: list[dict], auto_submit: bool, captcha: bool = False, form_errors: list[str] | None = None) -> tuple[bool, list[str]]:
    """Returns (submit_automatically, reasons_for_review)."""
    reasons: list[str] = []
    if not auto_submit:
        reasons.append("Auto-submit is turned off")
    if captcha:
        reasons.append("A CAPTCHA needs solving")
    for err in form_errors or []:
        reasons.append(f"Form error: {err}")
    for f in fields:
        filled = f.get("value") not in (None, "", [], False)
        if f.get("required") and not filled:
            reasons.append(f"Required field not filled: {f['label']}")
        elif filled and f.get("confidence", 0) < CONFIDENCE_THRESHOLD:
            reasons.append(f"Unsure about: {f['label']}")
    # De-duplicate while keeping order
    seen: set[str] = set()
    reasons = [r for r in reasons if not (r in seen or seen.add(r))]
    return (not reasons, reasons)
