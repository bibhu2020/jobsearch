import json
from fastapi import APIRouter
from pydantic import BaseModel
from agents.generate_agent import call_ai

router = APIRouter()


class ExtractRequest(BaseModel):
    content: str
    url: str | None = None


@router.post("/extract")
async def extract_job(req: ExtractRequest):
    system = "You are a job posting parser. Extract structured information from job posting text."
    user = f"""Extract job information from this content and return ONLY a JSON object:
{{
  "title": "Job title",
  "company": "Company name",
  "location": "Location or Remote",
  "description": "Full job description (keep it detailed, up to 2000 chars)"
}}

Content:
{req.content[:5000]}

URL: {req.url or "N/A"}
"""
    result = await call_ai(system, user, json_mode=True)
    try:
        return json.loads(result)
    except Exception:
        return {"title": "Position", "company": "Company", "location": "", "description": req.content[:2000]}
