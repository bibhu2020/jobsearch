import httpx


async def arbeitnow_source(queries: list[str]) -> list[dict]:
    results = []
    keywords = {w.lower() for q in queries for w in q.split() if len(w) > 3}
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get("https://www.arbeitnow.com/api/job-board-api")
            resp.raise_for_status()
            for job in resp.json().get("data", []):
                text = (job.get("title", "") + " " + job.get("description", "")).lower()
                if not keywords or any(kw in text for kw in keywords):
                    results.append({
                        "title": job.get("title", ""),
                        "company": job.get("company_name", ""),
                        "location": job.get("location", "Remote"),
                        "description": job.get("description", "")[:2000],
                        "url": job.get("url", ""),
                        "source": "arbeitnow",
                    })
                    if len(results) >= 20:
                        break
    except Exception as e:
        print(f"[arbeitnow] Error: {e}")
    return results
