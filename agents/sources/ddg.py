from duckduckgo_search import DDGS

JOB_DOMAINS = ("greenhouse.io", "lever.co", "ashbyhq.com", "workable.com",
               "smartrecruiters.com", "jobvite.com", "myworkdayjobs.com", "career")


async def ddg_source(queries: list[str]) -> list[dict]:
    results = []
    seen_urls = set()
    try:
        with DDGS() as ddgs:
            for query in queries:
                for r in ddgs.text(f"{query} remote job opening", max_results=10):
                    url = r.get("href", "")
                    if not url or url in seen_urls:
                        continue
                    if any(d in url.lower() for d in JOB_DOMAINS):
                        seen_urls.add(url)
                        results.append({
                            "title": r.get("title", ""),
                            "company": "",
                            "location": "Remote",
                            "description": r.get("body", "")[:1000],
                            "url": url,
                            "source": "ddg",
                        })
    except Exception as e:
        print(f"[ddg] Error: {e}")
    return results
