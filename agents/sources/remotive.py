import httpx


async def remotive_source(queries: list[str]) -> list[dict]:
    results = []
    keywords = " ".join(queries[:2]).replace('"', "").strip()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://remotive.com/api/remote-jobs",
                params={"search": keywords, "limit": 20},
            )
            resp.raise_for_status()
            jobs = resp.json().get("jobs", [])
            for job in jobs:
                results.append({
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "location": job.get("candidate_required_location", "Remote"),
                    "description": job.get("description", "")[:2000],
                    "url": job.get("url", ""),
                    "source": "remotive",
                })
    except Exception as e:
        print(f"[remotive] Error: {e}")
    return results
