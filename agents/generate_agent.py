import os
import json
from openai import AsyncOpenAI
from google import genai as google_genai
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_openai: AsyncOpenAI | None = None


def get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai


async def call_ai(system: str, user: str, json_mode: bool = False) -> str:
    prompt = f"{system}\n\n{user}"

    try:
        gemini = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        config = {"response_mime_type": "application/json"} if json_mode else {}
        resp = gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        return resp.text
    except Exception as e:
        print(f"Gemini failed ({e}), falling back to GPT-4o")
        try:
            kwargs = {"model": "gpt-4o", "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            client = get_openai()
            resp = await client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as ge:
            raise RuntimeError(f"Both AI providers failed. Gemini: {e}. OpenAI: {ge}")


class GenerateRequest(BaseModel):
    jobTitle: str = ""
    company: str = ""
    jobDescription: str = ""
    userProfile: dict = {}
    resumeText: str = ""


@router.post("/cover-letter")
async def generate_cover_letter(req: GenerateRequest):
    system = (
        "You are an expert career coach. Write a compelling, specific cover letter "
        "grounded entirely in the candidate's real experience. Never invent facts."
    )
    if req.resumeText.strip():
        user = f"""Write a tailored cover letter for this application.

TARGET ROLE:
{req.jobTitle} at {req.company}

JOB DESCRIPTION:
{req.jobDescription[:2000]}

CANDIDATE'S ACTUAL RESUME (use real companies, titles, and achievements — do not fabricate):
{req.resumeText[:4000]}

Instructions:
- 3–4 focused paragraphs, no generic filler
- Opening: why this specific company/role excites the candidate
- Middle paragraphs: cite 2–3 concrete achievements from their resume that directly address the JD requirements
- Closing: confident call to action
- Output in markdown. Start with 'Dear Hiring Manager,'"""
    else:
        user = f"""Write a cover letter for:

Job Title: {req.jobTitle}
Company: {req.company}

Job Description:
{req.jobDescription[:2000]}

Candidate Profile:
{json.dumps(req.userProfile, indent=2)[:2000]}

Write a professional cover letter (3–4 paragraphs) in markdown. Start with 'Dear Hiring Manager,'"""

    content = await call_ai(system, user)
    return {"content": content}


@router.post("/resume")
async def generate_resume(req: GenerateRequest):
    system = (
        "You are an expert resume writer. Your job is to rewrite a candidate's actual resume "
        "to better target a specific role — never invent or remove factual information."
    )
    if req.resumeText.strip():
        user = f"""Rewrite the candidate's resume below to target this specific job.

TARGET ROLE:
{req.jobTitle} at {req.company}

JOB DESCRIPTION (study the requirements carefully):
{req.jobDescription[:2500]}

CANDIDATE'S ACTUAL RESUME:
{req.resumeText[:5000]}

Rewriting rules — STRICTLY follow these:
1. Keep EVERY fact: company names, job titles, employment dates, real accomplishments
2. Do NOT invent new experiences, skills, or achievements
3. Reorder bullet points within each role to surface the most relevant achievements first
4. Rewrite bullet points to use keywords from the JD naturally (without keyword stuffing)
5. Rewrite the Summary (top section) to speak directly to this role and company
6. If the candidate has skills mentioned in the JD, make sure they appear in the Skills section
7. Output clean markdown: # Name, ## Summary, ## Skills, ## Experience, ## Education"""
    else:
        user = f"""Rewrite this candidate's resume to match the job description:

Job Title: {req.jobTitle}
Company: {req.company}

Job Description:
{req.jobDescription[:2500]}

Candidate Profile:
{json.dumps(req.userProfile, indent=2)[:2000]}

Output in markdown with sections: Summary, Skills, Experience, Education."""

    content = await call_ai(system, user)
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
