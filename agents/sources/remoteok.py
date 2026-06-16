import httpx


async def remoteok_source(queries: list[str]) -> list[dict]:
    results = []
    keywords = {w.lower() for q in queries for w in q.split()
                if len(w) > 3 and w.lower() not in ("remote", "jobs", "job", "senior", "junior", "the", "and")}
    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "Mozilla/5.0"}) as client:
            resp = await client.get("https://remoteok.com/api")
            resp.raise_for_status()
            data = resp.json()
            jobs = [j for j in data if isinstance(j, dict) and j.get("position")]
            for job in jobs:
                job_text = (job.get("position", "") + " " + " ".join(job.get("tags", []))).lower()
                if not keywords or any(kw in job_text for kw in keywords):
                    results.append({
                        "title": job.get("position", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", "Remote") or "Remote",
                        "description": job.get("description", "")[:2000],
                        "url": job.get("url", ""),
                        "source": "remoteok",
                    })
                if len(results) >= 25:
                    break
    except Exception as e:
        print(f"[remoteok] Error: {e}")
    return results
