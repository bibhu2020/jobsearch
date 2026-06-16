import urllib.parse
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def _query_to_slug(query: str) -> str:
    """Convert 'Azure DevOps Engineer' → 'azure-devops-engineer'."""
    return "-".join(query.lower().split())[:60]


async def wellfound_source(queries: list[str], country: str = "") -> list[dict]:
    results = []
    seen = set()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 900})
            page = await ctx.new_page()

            for query in queries[:3]:
                try:
                    slug = _query_to_slug(query)
                    url = f"https://wellfound.com/role/r/{slug}?remote=true"
                    await page.goto(url, timeout=30000)
                    await page.wait_for_timeout(3000)

                    # Check for login wall
                    body_text = await page.inner_text("body")
                    if "sign in" in body_text.lower() and len(body_text) < 2000:
                        print(f"[wellfound] login wall hit for {query}")
                        break

                    cards = await page.query_selector_all('[class*="JobListing"], [class*="job-listing"], [data-testid="job-listing"]')
                    if not cards:
                        cards = await page.query_selector_all('a[href*="/jobs/"]')

                    for card in cards:
                        try:
                            t_el  = await card.query_selector('h2, h3, [class*="title"], [class*="JobTitle"]')
                            co_el = await card.query_selector('[class*="company"], [class*="Company"], span[class*="name"]')
                            lo_el = await card.query_selector('[class*="location"], [class*="Location"]')

                            title    = (await t_el.inner_text()).strip()   if t_el  else ""
                            company  = (await co_el.inner_text()).strip()  if co_el else ""
                            location = (await lo_el.inner_text()).strip()  if lo_el else ""
                            href     = await card.get_attribute("href")    if not t_el else ""
                            if not href:
                                a_el = await card.query_selector("a[href]")
                                href = await a_el.get_attribute("href") if a_el else ""

                            if title and href and href not in seen:
                                seen.add(href)
                                full_url = href if href.startswith("http") else f"https://wellfound.com{href}"
                                results.append({
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "description": f"{title} at {company} ({location})",
                                    "url": full_url,
                                    "source": "wellfound",
                                })
                        except Exception:
                            continue

                    if len(results) >= 30:
                        break
                except Exception as e:
                    print(f"[wellfound] query error: {e}")

            await browser.close()
    except Exception as e:
        print(f"[wellfound] Error: {e}")

    print(f"[wellfound] {len(results)} jobs found")
    return results
