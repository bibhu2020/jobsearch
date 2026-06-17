import os
import json
from openai import AsyncOpenAI
from google import genai as google_genai
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_openai: AsyncOpenAI | None = None

# Provider selection — set AI_PRIMARY_PROVIDER / AI_FALLBACK_PROVIDER to "google" or "openai"
PRIMARY_PROVIDER = os.getenv("AI_PRIMARY_PROVIDER", "google")
FALLBACK_PROVIDER = os.getenv("AI_FALLBACK_PROVIDER", "openai")

# Model overrides — defaults match the provider defaults above
GOOGLE_MODEL = os.getenv("GOOGLE_AI_MODEL", "gemma-4")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai


async def _call_google(prompt: str, json_mode: bool, max_tokens: int) -> str:
    client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    config = {"max_output_tokens": max_tokens}
    if json_mode:
        config["response_mime_type"] = "application/json"
    resp = client.models.generate_content(model=GOOGLE_MODEL, contents=prompt, config=config)
    return resp.text


async def _call_openai(system: str, user: str, json_mode: bool, max_tokens: int) -> str:
    kwargs = {"model": OPENAI_MODEL, "max_tokens": max_tokens, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = await get_openai().chat.completions.create(**kwargs)
    return resp.choices[0].message.content


async def _call_provider(provider: str, prompt: str, system: str, user: str, json_mode: bool, max_tokens: int) -> str:
    if provider == "google":
        return await _call_google(prompt, json_mode, max_tokens)
    if provider == "openai":
        return await _call_openai(system, user, json_mode, max_tokens)
    raise ValueError(f"Unknown AI provider: {provider!r}. Use 'google' or 'openai'.")


async def call_ai(system: str, user: str, json_mode: bool = False, max_tokens: int = 2048) -> str:
    prompt = f"{system}\n\n{user}"
    try:
        return await _call_provider(PRIMARY_PROVIDER, prompt, system, user, json_mode, max_tokens)
    except Exception as primary_err:
        print(f"{PRIMARY_PROVIDER} failed ({primary_err}), falling back to {FALLBACK_PROVIDER}")
        try:
            return await _call_provider(FALLBACK_PROVIDER, prompt, system, user, json_mode, max_tokens)
        except Exception as fallback_err:
            raise RuntimeError(
                f"Both AI providers failed. "
                f"{PRIMARY_PROVIDER}: {primary_err}. {FALLBACK_PROVIDER}: {fallback_err}"
            )


class GenerateRequest(BaseModel):
    jobTitle: str = ""
    company: str = ""
    jobDescription: str = ""
    userProfile: dict = {}
    resumeText: str = ""


@router.post("/cover-letter")
async def generate_cover_letter(req: GenerateRequest):
    system = (
        "You are an expert career coach and professional writer who crafts compelling, "
        "highly personalized cover letters that get candidates interviews. "
        "Every sentence must be grounded in the candidate's real experience — never fabricate facts, "
        "companies, titles, or achievements."
    )
    if req.resumeText.strip():
        user = f"""Write a compelling, tailored cover letter for this application.

## TARGET ROLE
**{req.jobTitle}** at **{req.company}**

## JOB DESCRIPTION
{req.jobDescription[:3000]}

## CANDIDATE'S RESUME (use ONLY facts from here — do not fabricate anything)
{req.resumeText[:5000]}

## OUTPUT FORMAT
Output in clean markdown, following this exact structure:

---

# [Extract candidate's full name from the resume]
[Extract email from resume] | [Extract phone from resume] | [Extract city/location from resume]

---

[Today's date in format: Month DD, YYYY]

Hiring Manager
{req.company}

Dear Hiring Manager,

**Opening paragraph** (3 sentences):
- Sentence 1: Name the specific role and express genuine interest — reference something concrete about {req.company} from the job description (their product, mission, tech stack, or stated values).
- Sentence 2: One crisp thesis — why the candidate is a strong match, naming their most relevant title/domain from the resume.
- Do NOT use clichés like "I am writing to express my interest" or "I would be a great fit."

**Second paragraph** (3–4 sentences):
- Lead with the candidate's single most impressive and relevant achievement from the resume.
- Directly connect it to a specific requirement or pain point stated in the job description.
- If the resume has numbers (percentages, dollar amounts, user counts, time saved), use them.
- Name the actual company and role from the resume.

**Third paragraph** (3–4 sentences):
- Bring in a second relevant skill or achievement from the resume.
- Show understanding of what challenges this role at {req.company} faces (based on the JD).
- Explain specifically how the candidate's background addresses those challenges.

**Closing paragraph** (2–3 sentences):
- Express enthusiasm for contributing to {req.company}'s goals.
- Request an interview with confidence — not desperation.
- Thank them briefly.

Sincerely,
[Candidate's Full Name]

---

RULES:
- Extract real name, email, phone, location from the resume — do not use placeholders
- Every achievement cited must exist in the resume
- Use keywords from the JD naturally throughout the letter
- Tone: confident, warm, professional — never generic or desperate"""
    else:
        user = f"""Write a cover letter for:

Job Title: {req.jobTitle}
Company: {req.company}

Job Description:
{req.jobDescription[:3000]}

Candidate Profile:
{json.dumps(req.userProfile, indent=2)[:2000]}

Output in markdown. Include: candidate name header, date, salutation, 4 focused paragraphs, and signature."""

    content = await call_ai(system, user, max_tokens=1500)
    return {"content": content}


@router.post("/resume")
async def generate_resume(req: GenerateRequest):
    system = (
        "You are a professional resume writer and ATS optimization expert. "
        "Your job is to rewrite a candidate's resume to be perfectly tailored for a specific job posting. "
        "ABSOLUTE RULES — never break these:\n"
        "1. NEVER invent or add facts, companies, titles, dates, skills, or achievements not in the original\n"
        "2. NEVER remove any company, role, or date from the original — all experience stays\n"
        "3. ALWAYS preserve the candidate's real name and contact information from the top of the resume\n"
        "4. Rewrite and reorder to surface the most relevant experience first within each role\n"
        "5. Use exact keywords from the job description naturally — no stuffing"
    )
    if req.resumeText.strip():
        user = f"""Rewrite the candidate's resume to perfectly target this role.

## TARGET ROLE
**{req.jobTitle}** at **{req.company}**

## JOB DESCRIPTION — study every requirement, keyword, and technology mentioned
{req.jobDescription[:3500]}

## CANDIDATE'S ORIGINAL RESUME — this is the source of truth
{req.resumeText[:6000]}

## REQUIRED OUTPUT FORMAT
Output the complete resume in clean markdown, following this exact structure:

---

# [Candidate's Full Name — extract from top of resume]
[Email] | [Phone] | [City, State/Country] | [LinkedIn URL if present] | [GitHub/Portfolio if present]

---

## Professional Summary
3–4 sentences. Open with the candidate's years of experience and strongest domain. Reference the target role ({req.jobTitle}) and company ({req.company}) if natural. Close with what they bring that directly addresses the JD's top requirements. Use keywords from the JD.

## Core Competencies
Organize skills into 2–4 labeled groups that match what the JD values. Only include skills the candidate actually has.
**[Category 1 label]:** skill, skill, skill
**[Category 2 label]:** skill, skill, skill
(add more categories if needed)

---

## Professional Experience

### [Exact Job Title from resume] | [Exact Company Name] | [City, State] | [Start Month Year] – [End Month Year or Present]
- [Most relevant to {req.jobTitle}] Start with strong action verb. State what was done, the scale/technology, and the measurable result. Use JD keywords naturally.
- [Second most relevant] Same format — action verb, context, result.
- [Continue for all original bullets, rewritten and reordered by relevance]
- Keep 3–6 bullets per role. Reorder so most JD-relevant points come first.

[Repeat ### block for EVERY position in the original resume, most recent first]

---

## Education
### [Degree Name] | [Institution] | [Graduation Year or Expected Year]
[Optional: GPA if 3.5+, honors, relevant coursework only if it strengthens the application]

[## Certifications — include this section ONLY if certifications exist in the original resume]
- [Certification Name] — [Issuer] ([Year])

---

## REWRITING RULES
- Extract real name, email, phone, location from the original resume — no placeholders
- For each bullet: lead with a strong action verb, weave in 1–2 JD keywords, end with a result/impact
- If the original has numbers (%, $, time saved, team size, user count), keep and surface them prominently
- If no numbers exist for a bullet, still rewrite it clearly with context and scope
- The Summary must directly reference the target company and role — make it feel written specifically for this application
- Do not add a line for skills the candidate does not have"""
    else:
        user = f"""Create a tailored resume for:

Job Title: {req.jobTitle}
Company: {req.company}

Job Description:
{req.jobDescription[:3500]}

Candidate Profile:
{json.dumps(req.userProfile, indent=2)[:3000]}

Output complete resume in markdown: Name/Contact header, Professional Summary, Core Competencies, Professional Experience (with bullet points), Education."""

    content = await call_ai(system, user, max_tokens=3000)
    return {"content": content}


@router.post("/interview-questions")
async def generate_interview_questions(req: GenerateRequest):
    system = (
        "You are an expert interview coach. Generate the 5 most likely interview questions "
        "for this specific role, with detailed suggested answers for each."
    )
    user = f"""Generate 5 likely interview questions with suggested answers for:

Job Title: {req.jobTitle}
Company: {req.company}

Job Description:
{req.jobDescription[:3000]}

Format as markdown with each question as a ## heading followed by a suggested answer."""

    content = await call_ai(system, user)
    return {"content": content}


@router.post("/company-brief")
async def generate_company_brief(req: GenerateRequest):
    system = (
        "You are a business analyst helping a job candidate prepare for their interview. "
        "Create a concise, one-page company brief in markdown format."
    )
    user = f"""Create a one-page company brief for an interview preparation:

Company: {req.company}
Role: {req.jobTitle}

Job Description context:
{req.jobDescription[:2000]}

Include: Company Overview, Products/Services, Culture & Values, Recent News/Trends, Key Talking Points for the Interview."""

    content = await call_ai(system, user)
    return {"content": content}
