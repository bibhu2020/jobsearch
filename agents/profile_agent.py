import json
import pdfplumber
import docx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.generate_agent import call_ai

router = APIRouter()


class AnalyzeRequest(BaseModel):
    resumeText: str
    linkedinUrl: str | None = None


@router.post("/analyze")
async def analyze_profile(req: AnalyzeRequest):
    if not req.resumeText.strip():
        raise HTTPException(status_code=400, detail="Resume text is empty")

    system = (
        "You are an expert career analyst and resume parser. "
        "Extract structured information from the provided resume text and return ONLY valid JSON."
    )
    user = f"""Analyze this resume and extract the following as a JSON object:
{{
  "summary": "2-3 paragraph professional summary",
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {{"title": "", "company": "", "duration": "", "description": ""}}
  ],
  "education": [
    {{"degree": "", "school": "", "year": ""}}
  ]
}}

Resume:
{req.resumeText[:6000]}

{"LinkedIn URL: " + req.linkedinUrl if req.linkedinUrl else ""}
"""

    content = await call_ai(system, user, json_mode=True)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
