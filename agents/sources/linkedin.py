import urllib.parse
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


async def linkedin_source(queries: list[str]) -> list[dict]:
    results = []
    seen = set()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 800})
            page = await ctx.new_page()

            for query in queries[:3]:
                try:
                    q = urllib.parse.quote_plus(query)
                    url = (
                        f"https://www.linkedin.com/jobs/search/"
                        f"?keywords={q}&f_TPR=r604800&f_WT=2"   # last 7 days, remote
                    )
                    await page.goto(url, timeout=25000)
                    await page.wait_for_timeout(2000)

                    for card in await page.query_selector_all('.base-card'):
                        try:
                            t_el  = await card.query_selector('.base-search-card__title')
                            co_el = await card.query_selector('.base-search-card__subtitle')
                            lo_el = await card.query_selector('.job-search-card__location')
                            a_el  = await card.query_selector('a.base-card__full-link')

                            title    = (await t_el.inner_text()).strip()  if t_el  else ""
                            company  = (await co_el.inner_text()).strip() if co_el else ""
                            location = (await lo_el.inner_text()).strip() if lo_el else ""
                            href     = await a_el.get_attribute('href')   if a_el  else ""
                            clean_url = href.split('?')[0] if href else ""

                            if title and clean_url and clean_url not in seen:
                                seen.add(clean_url)
                                results.append({
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "description": f"{title} at {company} ({location})",
                                    "url": clean_url,
                                    "source": "linkedin",
                                })
                        except Exception:
                            continue

                    if len(results) >= 25:
                        break
                except Exception as e:
                    print(f"[linkedin] query error: {e}")

            await browser.close()
    except Exception as e:
        print(f"[linkedin] Error: {e}")

    print(f"[linkedin] {len(results)} jobs found")
    return results
