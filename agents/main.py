import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (works for local dev; HF injects secrets as env vars)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.profile_agent import router as profile_router
from agents.search_agent import router as search_router
from agents.generate_agent import router as generate_router
from agents.pdf_agent import router as pdf_router
from agents.jobs_agent import router as jobs_router
from agents.interviewer_agent import router as interviewer_router

app = FastAPI(title="Linear Lantern Agents", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Agents are only called by the NestJS gateway (same container in prod).
    # Wildcard is safe here; the gateway enforces auth before proxying.
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router, prefix="/profile", tags=["profile"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(generate_router, prefix="/generate", tags=["generate"])
app.include_router(pdf_router, prefix="/pdf", tags=["pdf"])
app.include_router(interviewer_router, prefix="/interviewer", tags=["interviewer"])


@app.get("/health")
async def health():
    return {"status": "ok"}
