#!/usr/bin/env python3
"""
Standalone job search script for GitHub Actions.
User context (profile, skills, experience) is passed in via environment variables
by the gateway when the logged-in user triggers the workflow dispatch.
Results are saved to search_results/{user_id}/YYYY-MM-DD.json.
"""
import sys
import os
import asyncio
import json
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from agents.search_agent import build_queries, deduplicate, score_and_rank, SearchRequest
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


async def run():
    raw_user_id = os.getenv("USER_ID", "").strip()
    if not raw_user_id:
        print("USER_ID not set — this workflow must be triggered by a logged-in user via the app.")
        sys.exit(1)

    user_id = int(raw_user_id)
    profile_summary = os.getenv("PROFILE_SUMMARY", "").strip()
    keywords = os.getenv("SEARCH_KEYWORDS", "").strip()
    location = os.getenv("SEARCH_LOCATION", "").strip()

    try:
        skills = json.loads(os.getenv("SKILLS", "[]"))
        if not isinstance(skills, list):
            skills = []
    except Exception:
        skills = []

    try:
        experience = json.loads(os.getenv("EXPERIENCE", "[]"))
        if not isinstance(experience, list):
            experience = []
    except Exception:
        experience = []

    if not profile_summary and not keywords:
        print(f"User {user_id} has no profile summary and no keywords — nothing to search for.")
        sys.exit(0)

    print(f"Searching jobs for user {user_id} ...")
    req = SearchRequest(
        userId=user_id,
        profileSummary=profile_summary,
        skills=skills,
        experience=experience,
        keywords=keywords,
        location=location,
        country=location,
    )

    queries = await build_queries(req)
    print(f"Queries: {queries}")

    results = await asyncio.gather(
        remotive_source(queries),
        dice_source(queries, location),
        builtin_source(queries, location),
        wellfound_source(queries, location),
        linkedin_source(queries),
        remote100k_source(queries, location),
        remoterocketship_source(queries, location),
        weworkremotely_source(queries),
        remoteok_source(queries),
        indeed_source(queries),
        return_exceptions=True,
    )

    source_names = [
        "remotive", "dice", "builtin", "wellfound", "linkedin",
        "remote100k", "remoterocketship", "weworkremotely", "remoteok", "indeed",
    ]
    MAX_PER_SOURCE = 6
    all_jobs = []
    for name, r in zip(source_names, results):
        if isinstance(r, list):
            capped = r[:MAX_PER_SOURCE]
            print(f"  {name}: {len(r)} found, using {len(capped)}")
            all_jobs.extend(capped)
        elif isinstance(r, Exception):
            print(f"  {name} error: {r}")

    unique_jobs = deduplicate(all_jobs)
    print(f"{len(unique_jobs)} unique jobs before ranking")

    top = await score_and_rank(unique_jobs, req)
    for job in top:
        job["user_id"] = user_id
        job["search_date"] = str(date.today())

    base_dir = os.getenv("SEARCH_RESULTS_PATH", "./search_results")
    out_dir = os.path.join(base_dir, str(user_id))
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{date.today()}.json")
    with open(out_file, "w") as f:
        json.dump(top, f, indent=2)

    print(f"\n✓ {len(top)} jobs saved to {out_file}")


if __name__ == "__main__":
    asyncio.run(run())
