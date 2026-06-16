import feedparser
import re


async def weworkremotely_source(queries: list[str]) -> list[dict]:
    results = []
    seen = set()
    keywords = {w.lower() for q in queries for w in q.split() if len(w) > 3}
    try:
        feed = feedparser.parse("https://weworkremotely.com/remote-jobs.rss")
        for entry in feed.entries:
            link = entry.get("link", "")
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = (title + " " + summary).lower()
            if link in seen:
                continue
            if keywords and not any(kw in text for kw in keywords):
                continue
            seen.add(link)
            # Title format: "[Category] Company: Job Title"
            clean = re.sub(r"^\[.*?\]\s*", "", title)
            parts = clean.split(":", 1)
            company = parts[0].strip() if len(parts) > 1 else ""
            job_title = parts[1].strip() if len(parts) > 1 else clean.strip()
            results.append({
                "title": job_title,
                "company": company,
                "location": "Remote",
                "description": re.sub(r"<[^>]+>", " ", summary)[:2000],
                "url": link,
                "source": "weworkremotely",
            })
            if len(results) >= 20:
                break
    except Exception as e:
        print(f"[weworkremotely] Error: {e}")
    return results
