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
        "You are a senior resume writer, ATS expert, and executive career coach. "
        "You produce complete, polished, senior-professional resumes tailored to a specific job posting.\n\n"
        "ABSOLUTE RULES — violating any of these is a failure:\n"
        "1. NEVER invent or add any fact not in the original resume (no fake companies, titles, dates, skills, achievements)\n"
        "2. NEVER drop any role from the last 10 years — every position must appear, no matter what\n"
        "3. ALWAYS include Education — even if only a degree and school name\n"
        "4. ALWAYS include Certifications & Professional Development if any exist in the original\n"
        "5. ALWAYS preserve the candidate's real name and contact info exactly as found\n"
        "6. Rewrite bullets to surface technical depth, domain expertise, process knowledge, and leadership impact\n"
        "7. Use keywords from the JD naturally — do not stuff"
    )
    if req.resumeText.strip():
        user = f"""Rewrite this candidate's complete resume to target the role below.

## TARGET ROLE
**{req.jobTitle}** at **{req.company}**

## JOB DESCRIPTION — extract every required skill, technology, domain, and process keyword
{req.jobDescription[:4000]}

## CANDIDATE'S ORIGINAL RESUME — complete source of truth, do not omit anything
{req.resumeText[:10000]}

---

## REQUIRED OUTPUT — follow this structure exactly, section by section

### SECTION 1 — Header
# [Candidate's Full Name]
[Email] | [Phone] | [City, State/Country] | [LinkedIn if present] | [GitHub/Portfolio if present]

---

### SECTION 2 — Professional Summary (4–5 sentences, REQUIRED)
Write a powerful senior-level summary that:
- Opens with total years of experience, primary technical domain, and industry/business domain
- Names 2–3 of the candidate's strongest technical capabilities that match the JD
- Calls out their domain expertise (industry verticals, business functions they've worked in)
- Mentions leadership or management scope (team size, stakeholders, budget if in resume)
- Closes by connecting their background to the specific needs of {req.company} / {req.jobTitle}
- Use keywords from the JD. Do NOT use phrases like "seasoned professional" or "results-driven."

### SECTION 3 — Core Competencies (REQUIRED, use ALL FOUR categories)
Populate every category using ONLY skills found in the original resume:

**Technical Skills:** [languages, frameworks, platforms, databases, cloud, tools, APIs]
**Domain & Industry Expertise:** [industries, business domains, functional areas the candidate has worked in]
**Methodologies & Processes:** [Agile, Scrum, DevOps, CI/CD, SDLC, SAFe, ITIL, or other processes from resume]
**Leadership & Management:** [team leadership, stakeholder management, mentoring, cross-functional, budget, P&L, etc.]

If a category has nothing in the original resume, write "N/A" rather than leaving it out.

---

### SECTION 4 — Professional Experience (REQUIRED — include EVERY role from the last 10 years)
List roles in reverse chronological order. For EACH role:

#### [Exact Job Title] | [Exact Company Name] | [City, Country] | [Start Mon YYYY] – [End Mon YYYY or Present]
- **[Technical]** [Most relevant technical achievement for this JD — action verb + technology/tool + scale + result]
- **[Domain]** [Achievement showing domain/industry/business expertise — what business problem was solved]
- **[Process]** [Achievement showing process, methodology, or operational improvement]
- **[Leadership]** [Achievement showing leadership, team impact, stakeholder influence, or org-level impact]
- [Additional bullets if original resume has more facts to surface — max 6 bullets per role]

Rule: Write 4–6 bullets per role. Always lead with technical depth, then domain knowledge, process, leadership.
Rewrite each bullet as: strong action verb → what was done (with technology/method) → measurable result or scope.
Keep all company names, titles, and dates EXACTLY as in the original. Do not infer or estimate dates.

---

### SECTION 5 — Education (REQUIRED — always include, never omit)
For each degree found in the original resume:
#### [Full Degree Name, e.g. Bachelor of Engineering in Computer Science] | [University/Institution Name] | [Year]
[Include GPA only if 3.5+ AND it appears in the original. Include honors/distinction if stated.]

### SECTION 6 — Certifications & Professional Development (REQUIRED if ANY exist in original resume)
List every certification, course, or training found in the original:
- **[Certification Name]** — [Issuing Body] | [Year if present]

If no certifications appear anywhere in the original resume, omit this section entirely.

---

## GLOBAL RULES
- Extract name/email/phone/location from the original — never use placeholders
- Do not shorten, skip, or summarize older roles — include all details from the last 10 years
- If a role is older than 10 years, include company name, title, and dates only (one line, no bullets)
- Numbers matter: if the resume has %, $, headcount, SLA, time saved — surface them prominently
- The Summary and bullets must feel written specifically for {req.jobTitle} at {req.company}, not generic"""
    else:
        user = f"""Create a complete tailored resume for:

Job Title: {req.jobTitle}
Company: {req.company}

Job Description:
{req.jobDescription[:4000]}

Candidate Profile:
{json.dumps(req.userProfile, indent=2)[:3000]}

Output a complete resume in markdown with: Header (name/contact), Professional Summary (4–5 sentences),
Core Competencies (Technical Skills / Domain & Industry / Methodologies & Processes / Leadership & Management),
Professional Experience (all roles with 4–6 bullets each), Education, Certifications if any."""

    content = await call_ai(system, user, max_tokens=4000)
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
