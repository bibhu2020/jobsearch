import urllib.parse
from playwright.async_api import async_playwright

JOB_HOSTS = ("greenhouse.io", "lever.co", "ashbyhq.com", "workable.com",
             "smartrecruiters.com", "jobvite.com", "myworkdayjobs.com")


async def google_playwright(queries: list[str]) -> list[dict]:
    results = []
    seen = set()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ))
            for query in queries[:2]:
                try:
                    site_filter = " OR ".join(f"site:{h}" for h in JOB_HOSTS[:4])
                    q = urllib.parse.quote_plus(f"{query} ({site_filter})")
                    await page.goto(f"https://www.google.com/search?q={q}&num=10", timeout=20000)
                    await page.wait_for_timeout(1500)

                    for link_el in await page.query_selector_all("a[href]"):
                        href = await link_el.get_attribute("href") or ""
                        if not any(h in href for h in JOB_HOSTS) or href in seen:
                            continue
                        h3 = await link_el.query_selector("h3")
                        title = (await h3.inner_text()).strip() if h3 else ""
                        if not title:
                            continue
                        seen.add(href)
                        results.append({
                            "title": title,
                            "company": "",
                            "location": "Remote",
                            "description": f"{title}",
                            "url": href,
                            "source": "google",
                        })
                except Exception as e:
                    print(f"[google_pw] query error: {e}")
            await browser.close()
    except Exception as e:
        print(f"[google_pw] Error: {e}")
    return results
