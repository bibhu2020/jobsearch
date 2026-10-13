"""Turns extracted form fields into answers.

Pass 1 — rules: map well-known questions onto the user's application defaults (confidence 1.0).
Pass 2 — LLM: everything else, answered from resume + job with a self-reported confidence.
Sensitive (legal / attestation / demographic) questions answered by the LLM are capped at 0.5
so they always go to the user for review.
"""
import difflib
import json
import re

from agents.generate_agent import call_ai

SENSITIVE_RE = re.compile(
    r"authori[sz]|sponsor|visa|criminal|convict|felony|background check|gender|sex\b|race|ethnic|hispanic|latin"
    r"|veteran|disabilit|pronoun|certify|attest|signature|sexual orientation|transgender|date of birth|\bage\b",
    re.I,
)
DECLINE_RE = re.compile(r"decline|prefer not|don.?t wish|do not wish|not to (say|answer|disclose)|rather not", re.I)

YES, NO = "Yes", "No"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*:?()\[\]]", " ", (text or "").lower())).strip()


def yes_no(flag: bool) -> str:
    return YES if flag else NO


# ── Option matching ─────────────────────────────────────────────────────────────

def match_option(value, options: list[str]) -> str | None:
    """Pick the option that best represents `value`; None when nothing fits."""
    if not options or value in (None, ""):
        return None
    v = norm(str(value))
    normed = [(o, norm(o)) for o in options if norm(o) and norm(o) not in ("select", "select...", "please select")]

    for o, n in normed:
        if n == v:
            return o
    if v in ("yes", "no"):
        for o, n in normed:
            if re.match(rf"^{v}\b", n):
                return o
        return None
    if DECLINE_RE.search(v):
        for o, n in normed:
            if DECLINE_RE.search(n):
                return o
        return None
    for o, n in normed:
        if n.startswith(v) or v.startswith(n):
            return o
    for o, n in normed:
        if v in n:
            return o
    best = difflib.get_close_matches(v, [n for _, n in normed], n=1, cutoff=0.6)
    if best:
        return next(o for o, n in normed if n == best[0])
    return None


# ── Rule pass ───────────────────────────────────────────────────────────────────

def _location(d: dict, profile: dict) -> str:
    parts = [d.get("city"), d.get("state"), d.get("country")]
    joined = ", ".join(p for p in parts if p)
    return joined or profile.get("location") or ""


COUNTRY_ALIASES = {
    "united states": ["united states", "u.s.", "usa", "us", "america"],
    "united kingdom": ["united kingdom", "uk", "britain", "england"],
    "india": ["india"],
    "canada": ["canada"],
}


def _mentions(text: str, country: str) -> bool:
    for alias in COUNTRY_ALIASES.get(country.lower(), [country.lower()]):
        if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", text.lower()):
            return True
    return False


def _work_authorization(label: str, d: dict, job_location: str) -> tuple[str, float] | None:
    countries = [c for c in d.get("workAuthorizedCountries") or [] if c]
    if not countries:
        return None
    if any(_mentions(label, c) for c in countries):
        return YES, 1.0
    if len(countries) == 1 and (not job_location or _mentions(job_location, countries[0]) or "remote" in job_location.lower()):
        # Label names no country; the job is in (or open to) the one country the user can work in.
        if not any(_mentions(label, c) for c in COUNTRY_ALIASES if c != countries[0].lower()):
            return YES, 0.9
    return None  # ambiguous → LLM (sensitive, so it goes to review)


def rule_answer(field: dict, ctx: dict) -> tuple[object, float] | None:
    """Returns (value, confidence) when a defaults rule covers this field."""
    label = norm(field.get("label", ""))
    d: dict = ctx.get("defaults") or {}
    profile: dict = ctx.get("profile") or {}
    ftype = field.get("type")

    def has(*words) -> bool:
        return any(re.search(w, label) for w in words)

    full_name = " ".join(p for p in [d.get("firstName"), d.get("lastName")] if p) or ctx.get("name") or ""

    if ftype == "file":
        return None
    if ftype == "checkbox":
        if has(r"privacy", r"consent", r"acknowledge", r"agree", r"terms", r"data (processing|protection)"):
            return True, 0.9
        return None
    if has(r"\bfirst name", r"given name", r"^first$"):
        return d.get("firstName"), 1.0
    if has(r"\blast name", r"surname", r"family name", r"^last$"):
        return d.get("lastName"), 1.0
    if has(r"preferred (first )?name", r"nickname"):
        return d.get("preferredName") or d.get("firstName"), 1.0
    if has(r"^(full |legal )?name$", r"^your name", r"full name", r"legal name"):
        return full_name, 1.0
    if has(r"e-?mail"):
        return ctx.get("email"), 1.0
    if has(r"phone", r"mobile", r"cell"):
        return d.get("phone"), 1.0
    if has(r"linkedin"):
        return d.get("linkedinUrl") or profile.get("linkedin_url"), 1.0
    if has(r"github"):
        return d.get("githubUrl"), 1.0
    if has(r"portfolio", r"personal (web)?site", r"^website", r"other website"):
        return d.get("portfolioUrl") or d.get("githubUrl"), 1.0
    if has(r"postal", r"zip"):
        return d.get("postalCode"), 1.0
    if has(r"^city$", r"^city\b"):
        return d.get("city"), 1.0
    if has(r"^(state|province)", r"state/province"):
        return d.get("state"), 1.0
    if has(r"^country$", r"country of residence"):
        return d.get("country"), 1.0
    if has(r"current location", r"where are you (currently )?(located|based)", r"^location$", r"^address$"):
        return _location(d, profile), 1.0
    if has(r"sponsor", r"visa"):
        if isinstance(d.get("requiresSponsorship"), bool):
            return yes_no(d["requiresSponsorship"]), 1.0
        return None
    if has(r"authori[sz]ed to work", r"eligib\w* to work", r"legally (able|permitted|authori[sz]ed)", r"right to work", r"work authori[sz]ation"):
        res = _work_authorization(field.get("label", ""), d, ctx.get("job_location", ""))
        return res
    if has(r"salary", r"compensation", r"pay expectation", r"desired pay"):
        if d.get("salaryExpectation"):
            amount = str(d["salaryExpectation"])
            return (amount if ftype in ("number",) else f"{amount} {d.get('salaryCurrency', '')}".strip()), 1.0
        return None
    if has(r"notice period"):
        return d.get("noticePeriod"), 1.0
    if has(r"start date", r"when can you start", r"available to start", r"earliest (start|available)"):
        return d.get("earliestStartDate") or d.get("noticePeriod"), 1.0
    if has(r"relocat"):
        if isinstance(d.get("willingToRelocate"), bool):
            return yes_no(d["willingToRelocate"]), 1.0
        return None
    if has(r"years of (professional |relevant |total |work )?experience") and not has(r" with ", r" in ", r" using "):
        return d.get("yearsExperience"), 1.0
    if has(r"highest (level of )?education", r"degree"):
        return d.get("highestEducation"), 1.0 if d.get("highestEducation") else 0
    if has(r"hispanic", r"latin[oxa]"):
        race = d.get("race") or "Decline to answer"
        if DECLINE_RE.search(race):
            return race, 1.0
        return yes_no("hispanic" in race.lower() or "latin" in race.lower()), 1.0
    if has(r"gender", r"^sex$"):
        return d.get("gender") or "Decline to answer", 1.0
    if has(r"\brace\b", r"ethnic"):
        return d.get("race") or "Decline to answer", 1.0
    if has(r"veteran"):
        return d.get("veteranStatus") or "Decline to answer", 1.0
    if has(r"disabilit"):
        return d.get("disabilityStatus") or "Decline to answer", 1.0
    if has(r"how did you (hear|find|learn)", r"where did you (hear|find)", r"^source$", r"referral source"):
        return "Job board", 0.9
    if has(r"cover letter") and ftype == "textarea" and ctx.get("cover_letter_text"):
        return ctx["cover_letter_text"], 0.9

    # Custom Q&A pairs saved in the profile
    custom = [(norm(qa.get("question", "")), qa.get("answer")) for qa in d.get("customAnswers") or [] if qa.get("question")]
    if custom:
        best = difflib.get_close_matches(label, [q for q, _ in custom], n=1, cutoff=0.75)
        if best:
            return next(a for q, a in custom if q == best[0]), 1.0
    return None


def apply_options(field: dict, value, confidence: float) -> tuple[object, float]:
    """Constrain a value to the field's options (select / radio / combobox / checkbox group)."""
    options = field.get("options") or []
    if not options or field.get("type") in ("checkbox",):
        return value, confidence
    if field.get("type") == "checkbox_group":
        values = value if isinstance(value, list) else [value]
        matched = [m for m in (match_option(v, options) for v in values) if m]
        return (matched, confidence) if matched else ([], 0)
    matched = match_option(value, options)
    return (matched, confidence) if matched else ("", 0)


# ── LLM pass ───────────────────────────────────────────────────────────────────

LLM_SYSTEM = (
    "You fill out job application forms on behalf of a candidate. Answer ONLY from the candidate data "
    "and job description provided. Never invent employers, dates, credentials or numbers. If the answer "
    "cannot be determined, return an empty value with confidence 0. For fields with options, the value "
    "must be one of the options verbatim (a list of options for checkbox_group). For free-text questions "
    "write a concise, specific, first-person answer (max 120 words). Confidence is your probability (0-1) "
    "that the candidate would give exactly this answer."
)


async def llm_answers(fields: list[dict], ctx: dict) -> dict[str, tuple[object, float]]:
    if not fields:
        return {}
    schema = [
        {k: f[k] for k in ("id", "label", "type", "required", "options") if f.get(k) not in (None, [], "")}
        for f in fields
    ]
    user = (
        f"## Job\n{ctx.get('job_title')} at {ctx.get('company')}\n{(ctx.get('job_description') or '')[:2500]}\n\n"
        f"## Candidate application defaults\n{json.dumps(ctx.get('defaults') or {}, ensure_ascii=False)[:2500]}\n\n"
        f"## Candidate profile\n{json.dumps(ctx.get('profile') or {}, ensure_ascii=False)[:2500]}\n\n"
        f"## Resume\n{(ctx.get('resume_text') or '')[:5000]}\n\n"
        f"## Fields to answer\n{json.dumps(schema, ensure_ascii=False)}\n\n"
        'Return JSON: {"answers": [{"id": "<field id>", "value": <string | list | true/false>, "confidence": <0-1>}]}'
    )
    try:
        raw = await call_ai(LLM_SYSTEM, user, json_mode=True, max_tokens=3000)
        data = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception as err:  # provider outage → fields stay unanswered and go to review
        print(f"apply: LLM answering failed ({err})")
        return {}
    out: dict[str, tuple[object, float]] = {}
    for a in data.get("answers", []):
        try:
            out[str(a["id"])] = (a.get("value"), float(a.get("confidence", 0)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


# ── Entry point ─────────────────────────────────────────────────────────────────

async def answer_fields(fields: list[dict], ctx: dict) -> None:
    """Fills `value`, `source`, `confidence`, `sensitive` on each field in place (skips ones already answered)."""
    pending: list[dict] = []
    for f in fields:
        if "value" in f and f.get("source"):
            continue
        f["sensitive"] = bool(SENSITIVE_RE.search(f.get("label", "")))
        if f.get("type") == "file":
            label = norm(f.get("label", ""))
            if re.search(r"resume|\bcv\b|curriculum", label) or (f.get("accept_resume") and "cover" not in label):
                f.update(value=ctx.get("resume_filename"), source="file", confidence=1.0)
            else:
                f.update(value="", source="file", confidence=0)
            continue
        rule = rule_answer(f, ctx)
        if rule and rule[0] not in (None, ""):
            value, conf = apply_options(f, *rule)
            if value not in ("", []):
                f.update(value=value, source="default", confidence=conf)
                continue
        pending.append(f)

    llm = await llm_answers(pending, ctx)
    for f in pending:
        value, conf = llm.get(f["id"], ("", 0))
        value, conf = apply_options(f, value, conf)
        if f["sensitive"]:
            conf = min(conf, 0.5)
        if value in (None,):
            value = ""
        f.update(value=value, source="llm", confidence=conf if value not in ("", []) else 0)
