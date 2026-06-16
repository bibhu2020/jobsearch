import feedparser
import urllib.parse


async def indeed_rss_source(queries: list[str]) -> list[dict]:
    results = []
    seen_urls = set()
    for query in queries[:2]:
        try:
            q = urllib.parse.quote_plus(query)
            url = f"https://www.indeed.com/rss?q={q}&l=remote&sort=date"
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                link = entry.get("link", "")
                if link and link not in seen_urls:
                    seen_urls.add(link)
                    summary = entry.get("summary", "")
                    results.append({
                        "title": entry.get("title", ""),
                        "company": entry.get("source", {}).get("title", ""),
                        "location": "",
                        "description": summary[:1500],
                        "url": link,
                        "source": "indeed",
                    })
        except Exception as e:
            print(f"[indeed_rss] Error for query '{query}': {e}")
    return results
