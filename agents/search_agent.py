import asyncio
import json
from fastapi import APIRouter
from pydantic import BaseModel
from agents.generate_agent import call_ai
from agents.sources.remotive import remotive_source
from agents.sources.remoteok import remoteok_source
from agents.sources.weworkremotely import weworkremotely_source
from agents.sources.linkedin import linkedin_source
from agents.sources.indeed import indeed_source
from agents.sources.dice import dice_source
from agents.sources.builtin import builtin_source
from agents.sources.wellfound import wellfound_source
from agents.sources.remote100k import remote100k_source
from agents.sources.remoterocketship import remoterocketship_source

router = APIRouter()


class SearchRequest(BaseModel):
    userId: int
    profileSummary: str = ""
    skills: list[str] = []
    experience: list[dict] = []
    keywords: str = ""
    location: str = ""
    country: str = ""   # browser-detected country, used as hard filter


async def build_queries(profile: SearchRequest) -> list[str]:
    geo = profile.country.strip() or profile.location.strip()
    loc_suffix = f" {geo}" if geo else " remote"

    if profile.keywords.strip():
        base = profile.keywords.strip()
        if geo:
            return [
                f"{base} remote {geo}",
                f"{base} remote",
                f"{base} {geo}",
                base,
            ]
        return [f"{base} remote", f"{base} remote worldwide", f"{base} engineer", base]

    if not profile.profileSummary and not profile.skills:
        return [f"software engineer{loc_suffix}", f"developer{loc_suffix}", f"engineer remote"]

    system = "You are a job search expert. Generate targeted job search queries."
    user = f"""Based on this candidate profile, generate 4 specific job search queries.
Return ONLY a JSON array of 4 strings, e.g. ["Senior Data Analyst remote UK", "BI Engineer SQL Python", "Analytics Manager", "Data Engineer AWS"]

Profile Summary: {profile.profileSummary[:1000]}
Skills: {", ".join(profile.skills[:15])}
Recent roles: {", ".join(e.get("title","") for e in profile.experience[:3] if e.get("title"))}
Location / Country: {geo or "not specified — include remote options"}
"""
    try:
        result = await call_ai(system, user, json_mode=True)
        parsed = json.loads(result)
        if isinstance(parsed, list):
            flat = parsed
        elif isinstance(parsed, dict):
            flat = next(
                (v for v in parsed.values() if isinstance(v, list) and all(isinstance(i, str) for i in v)),
                [str(v) for v in parsed.values()]
            )
        else:
            flat = []
        queries = [q for q in flat if isinstance(q, str) and q.strip()][:4]
        if queries:
            return queries
    except Exception as e:
        print(f"[build_queries] Error: {e}")

    title = profile.experience[0].get("title", "") if profile.experience else ""
    skill_str = " ".join(profile.skills[:3]) if profile.skills else "professional"
    return [
        f"{title}{loc_suffix}" if title else f"{skill_str}{loc_suffix}",
        f"{skill_str} engineer",
        f"{title or skill_str} job",
        f"{skill_str} developer",
    ]


def deduplicate(jobs: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for job in jobs:
        key = (job.get("url") or f"{job.get('title','')}|{job.get('company','')}").lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


async def score_and_rank(jobs: list[dict], profile: SearchRequest) -> list[dict]:
    if not jobs:
        return []

    jobs_summary = "\n".join(
        f"{i+1}. {j['title']} at {j['company']} ({j['source']}): {(j['description'] or '')[:300]}"
        for i, j in enumerate(jobs[:60])
    )

    geo = profile.country.strip() or profile.location.strip()

    if profile.keywords.strip():
        context = profile.keywords.strip()
    else:
        context = f"Summary: {profile.profileSummary[:600]}\nSkills: {', '.join(profile.skills[:15])}"

    country_instruction = ""
    if geo:
        country_instruction = f"""
COUNTRY FILTER (STRICT): The candidate is based in {geo}.
- Score jobs that are "remote worldwide", "remote — anywhere", or explicitly open to {geo} candidates normally.
- Score jobs restricted to a DIFFERENT country (e.g. "US only", "EU only", "UK only" when the candidate is NOT in that region) below 40 — these are a poor fit regardless of skills.
- If a job has no country restriction and is remote, assume it's available to this candidate.
"""

    system = "You are a senior career advisor doing rigorous job-candidate matching."
    user = f"""Candidate profile:
{context}
{country_instruction}
Job listings (numbered):
{jobs_summary}

Evaluate every listing against the candidate. Select ONLY the TOP 5 best matches that are realistically accessible to this candidate.
For each, provide an honest percentage match score (0-100), list what specifically matches,
list real gaps or concerns, and give a clear recommendation.

Return a JSON object — no markdown, no explanation outside JSON:
{{
  "selections": [
    {{
      "index": 1,
      "match_score": 82,
      "matching": ["3+ years Python matches requirement", "Remote position fits preference", "Fintech domain experience"],
      "gaps": ["Requires TypeScript — not in profile", "Lead role needs management experience"],
      "recommendation": "apply",
      "match_reason": "Strong Python backend match. Fintech experience is a differentiator. TypeScript gap is bridgeable."
    }}
  ]
}}

recommendation must be one of: "apply" (score>=70, strong fit), "consider" (50-69, partial fit), "skip" (<50 or critical gaps or country mismatch).
Be honest — do not recommend applying for jobs with hard requirements the candidate clearly lacks.
"""
    try:
        result = await call_ai(system, user, json_mode=True)
        parsed = json.loads(result)
        selections = parsed.get("selections", [])
        top = []
        for sel in selections[:5]:
            idx = sel.get("index", 1) - 1
            if 0 <= idx < len(jobs):
                job = jobs[idx].copy()
                job["match_score"] = int(sel.get("match_score", 50))
                job["matching"] = sel.get("matching", [])
                job["gaps"] = sel.get("gaps", [])
                job["recommendation"] = sel.get("recommendation", "consider")
                job["match_reason"] = sel.get("match_reason", "")
                top.append(job)
        return [j for j in top if j.get("match_score", 0) >= 70]
    except Exception as e:
        print(f"[score_and_rank] Error: {e}")
        return []


@router.post("/jobs")
async def search_jobs(req: SearchRequest):
    queries = await build_queries(req)
    country = req.country.strip()
    print(f"[search] Queries: {queries} | Country: {country or 'unspecified'}")

    results = await asyncio.gather(
        # Tier 1 — highest signal
        remotive_source(queries),
        dice_source(queries, country),
        builtin_source(queries, country),
        wellfound_source(queries, country),
        linkedin_source(queries),
        # Tier 2 — vetted senior / remote
        remote100k_source(queries, country),
        remoterocketship_source(queries, country),
        weworkremotely_source(queries),
        remoteok_source(queries),
        # Tier 3 — broad discovery
        indeed_source(queries),
        return_exceptions=True,
    )

    source_names = [
        "remotive", "dice", "builtin", "wellfound", "linkedin",
        "remote100k", "remoterocketship", "weworkremotely", "remoteok", "indeed",
    ]
    # Cap each source equally so high-volume sources (LinkedIn, Indeed) don't crowd out others
    MAX_PER_SOURCE = 6
    all_jobs = []
    for name, r in zip(source_names, results):
        if isinstance(r, list):
            capped = r[:MAX_PER_SOURCE]
            print(f"[search] {name}: {len(r)} found, using {len(capped)}")
            all_jobs.extend(capped)
        elif isinstance(r, Exception):
            print(f"[search] {name} error: {r}")

    unique_jobs = deduplicate(all_jobs)
    print(f"[search] {len(unique_jobs)} unique jobs total")

    top = await score_and_rank(unique_jobs, req)
    return {"jobs": top, "total_found": len(unique_jobs)}
