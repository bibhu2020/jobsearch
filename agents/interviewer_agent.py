import os
import json
from fastapi import APIRouter
from pydantic import BaseModel
from openai import AsyncOpenAI
from google import genai as google_genai

router = APIRouter()

PRIMARY_PROVIDER = os.getenv("AI_PRIMARY_PROVIDER", "google")
GOOGLE_MODEL = os.getenv("GOOGLE_AI_MODEL", "gemma-4")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

_openai: AsyncOpenAI | None = None


def get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai


async def _call_ai(prompt: str) -> str:
    try:
        if PRIMARY_PROVIDER == "google" and os.getenv("GEMINI_API_KEY"):
            client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            resp = client.models.generate_content(
                model=GOOGLE_MODEL,
                contents=prompt,
                config={"max_output_tokens": 1500, "response_mime_type": "application/json"},
            )
            return resp.text
    except Exception:
        pass

    client = get_openai()
    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=1500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a hiring assistant. Respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content


class ExtractRequest(BaseModel):
    resume_text: str


@router.post("/extract-candidate")
async def extract_candidate(body: ExtractRequest):
    prompt = f"""Extract the candidate's personal contact information from this resume.

Resume (first 3000 chars):
{body.resume_text[:3000]}

Return a JSON object with exactly these keys:
- "name": full name of the candidate (string — infer from email username if not obvious, never null)
- "email": email address found in the resume (string or null)

Return ONLY the JSON, no explanation.
"""
    raw = await _call_ai(prompt)
    try:
        data = json.loads(raw)
    except Exception:
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        data = json.loads(m.group()) if m else {}

    return {
        "name": (data.get("name") or "").strip() or "Unknown Candidate",
        "email": (data.get("email") or "").strip() or None,
    }


class FormatJdRequest(BaseModel):
    text: str


@router.post("/format-jd")
async def format_jd(body: FormatJdRequest):
    prompt = f"""Format this job description as compact HTML for a rich text editor.

Input text:
{body.text[:6000]}

Return JSON: {{"html": "..."}}

HTML rules (strict):
- <h2>Section Name</h2> for content sections (Responsibilities, Requirements, Nice to Have, Benefits, etc.)
- <ul><li>item text</li></ul> for bullet lists — NO <p> inside <li>, text goes directly in <li>
- <p>text</p> for introductory overview paragraphs only
- <strong>term</strong> only for key technical terms when needed
- COMPACT: absolutely NO whitespace or newlines between tags — every tag immediately follows the last closing tag

SKIP these entirely — they are captured in separate form fields:
- Job title / role name lines
- Location / office / remote lines
- Experience level lines (e.g. "5-10 Years", "3+ years")
- Employment type lines (Full-Time, Contract, Part-Time)
- Salary / compensation lines
- Any single-word label + value pairs at the top of the JD

Preserve all responsibilities, requirements, and qualifications.

Example: {{"html": "<h2>About the Role</h2><p>We are seeking a senior engineer...</p><h2>Responsibilities</h2><ul><li>Design RESTful APIs</li><li>Build microservices</li></ul><h2>Requirements</h2><ul><li>5+ years Node.js</li><li>Experience with PostgreSQL</li></ul>"}}
"""
    raw = await _call_ai(prompt)

    import re
    # _call_ai returns JSON string — parse it to extract the html field
    try:
        data = json.loads(raw)
        html = data.get("html") or data.get("content") or data.get("result") or ""
    except Exception:
        # Fallback: AI returned raw HTML or something else
        html = raw
        html = re.sub(r'^```(?:html)?\s*', '', html.strip(), flags=re.IGNORECASE)
        html = re.sub(r'\s*```$', '', html)

    # Remove any remaining whitespace between tags that the AI snuck in
    html = re.sub(r'>\s+<', '><', html.strip())
    # Remove <p> wrappers inside <li> elements
    html = re.sub(r'<li>\s*<p>', '<li>', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>\s*</li>', '</li>', html, flags=re.IGNORECASE)
    # Remove empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html, flags=re.IGNORECASE)

    return {"html": html.strip()}


class ScanRequest(BaseModel):
    resume_text: str
    job_description: str = ""


@router.post("/scan-resume")
async def scan_resume(body: ScanRequest):
    jd_section = (
        f"\n\nJob Description:\n{body.job_description[:3000]}"
        if body.job_description.strip()
        else ""
    )

    prompt = f"""You are evaluating a candidate's resume for a hiring manager.

Resume:
{body.resume_text[:4000]}{jd_section}

Return a JSON object with these exact keys:
- "summary": 2-3 sentence professional summary of the candidate
- "score": integer 0-100 fit score (100 = perfect match)
- "matching": array of strings — top strengths or matching qualifications (max 5)
- "gaps": array of strings — missing skills or concerns (max 5)
- "recommendation": one of "strong_yes" | "yes" | "consider" | "no"

Base score on relevant skills, experience depth, and fit for the role{' described' if body.job_description.strip() else ' in general'}.
"""

    raw = await _call_ai(prompt)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        data = json.loads(m.group()) if m else {}

    return {
        "summary": data.get("summary", ""),
        "score": int(data.get("score", 0)),
        "matching": data.get("matching", []),
        "gaps": data.get("gaps", []),
        "recommendation": data.get("recommendation", "consider"),
    }
