import urllib.parse
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


async def dice_source(queries: list[str], country: str = "") -> list[dict]:
    results = []
    seen = set()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 900})
            page = await ctx.new_page()

            for query in queries[:3]:
                try:
                    q = urllib.parse.quote_plus(query)
                    url = (
                        f"https://www.dice.com/jobs?q={q}"
                        f"&location=Remote&radius=30&radiusUnit=mi"
                        f"&page=1&pageSize=20&filters.postedDate=ONE_WEEK&language=en"
                    )
                    await page.goto(url, timeout=30000)
                    await page.wait_for_timeout(3000)

                    cards = await page.query_selector_all("dhi-search-card")
                    for card in cards:
                        try:
                            t_el  = await card.query_selector('[data-cy="card-title-link"]')
                            co_el = await card.query_selector('[data-cy="search-result-company-name"]')
                            lo_el = await card.query_selector('.search-result-location, [data-cy="search-result-location"]')

                            title    = (await t_el.inner_text()).strip()  if t_el  else ""
                            company  = (await co_el.inner_text()).strip() if co_el else ""
                            location = (await lo_el.inner_text()).strip() if lo_el else ""
                            href     = await t_el.get_attribute("href")   if t_el  else ""

                            if title and href and href not in seen:
                                seen.add(href)
                                full_url = href if href.startswith("http") else f"https://www.dice.com{href}"
                                results.append({
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "description": f"{title} at {company} ({location})",
                                    "url": full_url,
                                    "source": "dice",
                                })
                        except Exception:
                            continue

                    if len(results) >= 30:
                        break
                except Exception as e:
                    print(f"[dice] query error: {e}")

            await browser.close()
    except Exception as e:
        print(f"[dice] Error: {e}")

    print(f"[dice] {len(results)} jobs found")
    return results
