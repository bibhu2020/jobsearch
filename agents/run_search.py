#!/usr/bin/env python3
"""
Standalone job search script for GitHub Actions.
Reads user profiles from SQLite, runs 5-source parallel search,
writes results to search_results/YYYY-MM-DD.json.
"""
import sys
import os
import asyncio
import json
from datetime import date

# Ensure project root is in path when called as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from agents.database import fetchall
from agents.search_agent import build_queries, deduplicate, score_and_rank, SearchRequest


async def run():
    users = await fetchall(
        """SELECT u.id as user_id, up.profile_summary, up.skills, up.experience
           FROM users u
           JOIN user_profiles up ON u.id = up.user_id
           WHERE up.profile_summary IS NOT NULL"""
    )

    if not users:
        print("No users with analyzed profiles found.")
        return

    all_results = []
    for user in users:
        print(f"Searching jobs for user {user['user_id']}...")
        req = SearchRequest(
            userId=user["user_id"],
            profileSummary=user["profile_summary"] or "",
            skills=json.loads(user["skills"] or "[]"),
            experience=json.loads(user["experience"] or "[]"),
        )
        queries = await build_queries(req)

        from agents.sources.remotive import remotive_source
        from agents.sources.arbeitnow import arbeitnow_source
        from agents.sources.ddg import ddg_source
        from agents.sources.indeed_rss import indeed_rss_source
        from agents.sources.google_pw import google_playwright

        results = await asyncio.gather(
            remotive_source(queries),
            arbeitnow_source(queries),
            ddg_source(queries),
            indeed_rss_source(queries),
            google_playwright(queries),
            return_exceptions=True,
        )

        all_jobs = []
        for r in results:
            if isinstance(r, list):
                all_jobs.extend(r)

        unique_jobs = deduplicate(all_jobs)
        top5 = await score_and_rank(unique_jobs, req)

        for job in top5:
            job["user_id"] = user["user_id"]
            job["search_date"] = str(date.today())

        all_results.extend(top5)
        print(f"  → {len(top5)} top jobs found")

    out_dir = os.getenv("SEARCH_RESULTS_PATH", "./search_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{date.today()}.json")
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✓ Results saved to {out_file}")


if __name__ == "__main__":
    asyncio.run(run())
