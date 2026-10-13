"""Offline checks for the auto-apply logic. Run: PYTHONPATH=. python3 -m agents.apply.selftest"""
import asyncio
import shutil

from agents.apply import detect, gate, gmail, verification
from agents.apply.manager import Run
from agents.apply.answers import apply_options, match_option, rule_answer

DEFAULTS = {
    "firstName": "Ada", "lastName": "Lovelace", "phone": "+1 555 0100",
    "city": "Seattle", "state": "WA", "country": "United States",
    "linkedinUrl": "https://linkedin.com/in/ada", "githubUrl": "https://github.com/ada",
    "workAuthorizedCountries": ["United States"], "requiresSponsorship": False,
    "salaryExpectation": "180000", "salaryCurrency": "USD", "willingToRelocate": True,
    "yearsExperience": "10", "gender": "Decline to answer", "race": "Decline to answer",
    "veteranStatus": "I am not a protected veteran", "disabilityStatus": "Decline to answer",
    "customAnswers": [{"question": "Are you open to working in the Pacific time zone?", "answer": "Yes"}],
}
CTX = {"defaults": DEFAULTS, "profile": {}, "email": "ada@example.com", "job_location": "Remote - US"}


def field(label, type_="text", options=None, required=True):
    return {"id": "1", "label": label, "type": type_, "options": options or [], "required": required}


def check_rules():
    cases = [
        (field("First Name"), "Ada"),
        (field("Last Name"), "Lovelace"),
        (field("Full name"), "Ada Lovelace"),
        (field("Email"), "ada@example.com"),
        (field("Phone"), "+1 555 0100"),
        (field("LinkedIn Profile"), "https://linkedin.com/in/ada"),
        (field("Will you now or in the future require sponsorship for employment visa status?", "select", ["Yes", "No"]), "No"),
        (field("Are you legally authorized to work in the United States?", "radio", ["Yes", "No"]), "Yes"),
        (field("Are you willing to relocate?", "select", ["Yes", "No"]), "Yes"),
        (field("Gender", "select", ["Male", "Female", "I don't wish to answer"]), "I don't wish to answer"),
        (field("Veteran Status", "select", ["I am a protected veteran", "I am not a protected veteran", "I don't wish to answer"]), "I am not a protected veteran"),
        (field("Are you open to working in the Pacific time zone"), "Yes"),
        (field("I agree to the privacy policy", "checkbox"), True),
    ]
    for f, expected in cases:
        rule = rule_answer(f, CTX)
        assert rule, f"no rule for {f['label']!r}"
        value, conf = apply_options(f, *rule)
        assert value == expected, f"{f['label']!r}: got {value!r}, expected {expected!r}"
        assert conf >= 0.8, f"{f['label']!r}: low confidence {conf}"

    # Skill-specific experience questions are left to the LLM
    assert rule_answer(field("Years of experience with Kubernetes"), CTX) is None
    # Checkboxes never receive text answers
    assert rule_answer(field("Email me about future openings", "checkbox"), CTX) is None
    # Authorization for a country the user isn't authorized in → not answered by rules
    assert rule_answer(field("Are you authorized to work in Germany?", "radio", ["Yes", "No"]),
                       {**CTX, "job_location": "Berlin, Germany"}) is None


def check_options():
    assert match_option("No", ["Yes", "No"]) == "No"
    assert match_option("Yes", ["Yes, I am authorized", "No, I am not"]) == "Yes, I am authorized"
    assert match_option("Decline to answer", ["Male", "Female", "Prefer not to say"]) == "Prefer not to say"
    assert match_option("United States", ["Canada", "United States of America"]) == "United States of America"
    assert match_option("Klingon", ["Yes", "No"]) is None


def check_gate():
    good = [{"label": "Name", "type": "text", "required": True, "value": "Ada", "confidence": 1.0}]
    assert gate.decide(good, auto_submit=True) == (True, [])
    assert gate.decide(good, auto_submit=False)[0] is False
    assert gate.decide(good, auto_submit=True, captcha=True)[0] is False
    unsure = good + [{"label": "Why us?", "type": "textarea", "required": False, "value": "...", "confidence": 0.6}]
    ok, reasons = gate.decide(unsure, auto_submit=True)
    assert not ok and reasons == ["Unsure about: Why us?"]
    missing = good + [{"label": "Resume", "type": "file", "required": True, "value": "", "confidence": 0}]
    assert gate.decide(missing, auto_submit=True)[1] == ["Required field not filled: Resume"]
    optional_empty = good + [{"label": "Pronouns", "type": "text", "required": False, "value": "", "confidence": 0}]
    assert gate.decide(optional_empty, auto_submit=True)[0] is True


def check_detect():
    assert detect.site_for_url("https://boards.greenhouse.io/acme/jobs/123") == "greenhouse"
    assert detect.site_for_url("https://job-boards.greenhouse.io/acme/jobs/123") == "greenhouse"
    assert detect.site_for_url("https://acme.com/careers?gh_jid=123") == "greenhouse"
    assert detect.site_for_url("https://jobs.lever.co/acme/abc-123") == "lever"
    assert detect.site_for_url("https://jobs.ashbyhq.com/acme/abc") == "ashby"
    assert detect.site_for_url("https://www.linkedin.com/jobs/view/1") == "linkedin"
    assert detect.site_for_url("https://acme.wd5.myworkdayjobs.com/en-US/careers/job/1") == "workday"
    assert detect.site_for_url("https://acme.com/jobs/1") is None
    assert detect.embedded_form_url(["https://boards.greenhouse.io/embed/job_app?for=acme&token=1"])[0] == "greenhouse"
    assert detect.is_confirmation("https://x/confirmation", "", ("/confirmation",))
    assert detect.is_confirmation("https://x", "Thank you for applying to Acme!")
    assert detect.is_confirmation("https://x", "Your application has been submitted.")
    assert not detect.is_confirmation("https://x", "Apply for this job")
    assert detect.CLOSED_RE.search("Sorry, this position is no longer accepting applications")


def check_gmail():
    assert gmail.extract_code_or_link("Your verification code is 482913. It expires soon.") == {"code": "482913"}
    assert gmail.extract_code_or_link('Click <a href="https://acme.myworkdayjobs.com/verify?t=abc">here</a>') == \
        {"link": "https://acme.myworkdayjobs.com/verify?t=abc"}
    assert gmail.extract_code_or_link("Hello, thanks for your interest.") is None


async def _verify_with(gmail_behaviour, user_value):
    """Drive obtain_verification with a fake Gmail and a simulated user."""
    async def fake_wait(*_args, **_kw):
        if isinstance(gmail_behaviour, Exception):
            raise gmail_behaviour
        return gmail_behaviour

    original = gmail.wait_for_verification
    gmail.wait_for_verification = fake_wait
    try:
        run = Run({"run_id": "t", "applicant": {"email": "ada@example.com"},
                   "gmail": {"refresh_token": "x"} if gmail_behaviour is not None else None})
        task = asyncio.create_task(verification.obtain_verification(run, "myworkday.com", "Workday"))
        for _ in range(50):
            await asyncio.sleep(0.01)
            if task.done() or run.status == "needs_input":
                break
        asked = run.status == "needs_input"
        if asked:
            assert run.needs == {"kind": "verification", "email": "ada@example.com", "sender": "myworkday.com"}
            run.provided = user_value
            run.actions.put_nowait("resume")
        result = await task
        shutil.rmtree(run.workdir, ignore_errors=True)
        return result, asked, run
    finally:
        gmail.wait_for_verification = original


def check_verification():
    async def scenarios():
        # Gmail finds the code → user never asked
        result, asked, _ = await _verify_with({"code": "123456"}, None)
        assert result == {"code": "123456"} and not asked
        # No Gmail connected → user types the code
        result, asked, run = await _verify_with(None, " 482913 ")
        assert asked and result == {"code": "482913"} and run.needs is None
        # Gmail token expired → flagged for the gateway, user pastes a link
        result, asked, run = await _verify_with(gmail.GmailAuthError("invalid_grant"), "https://acme.myworkdayjobs.com/verify?t=1")
        assert asked and run.gmail_invalid and result == {"link": "https://acme.myworkdayjobs.com/verify?t=1"}
        # Nothing in Gmail, user finished it via take-over and just clicked Resume
        result, asked, _ = await _verify_with({}, None)
        assert asked and result == {"manual": True}
    asyncio.run(scenarios())


if __name__ == "__main__":
    for check in (check_rules, check_options, check_gate, check_detect, check_gmail, check_verification):
        check()
        print(f"✓ {check.__name__}")
    print("All auto-apply self-tests passed")
