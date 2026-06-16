import urllib.parse
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


async def builtin_source(queries: list[str], country: str = "") -> list[dict]:
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
                    url = f"https://builtin.com/jobs?search={q}&remote=true&t=job"
                    await page.goto(url, timeout=30000)
                    await page.wait_for_timeout(3000)

                    # BuiltIn job cards: each card is a <div> linking to the job
                    cards = await page.query_selector_all('[data-id][class*="job"]')
                    if not cards:
                        # fallback selector pattern
                        cards = await page.query_selector_all("article.job-listing, .job-card, [data-testid='job-card']")

                    for card in cards:
                        try:
                            t_el  = await card.query_selector("h2 a, h3 a, .job-title a, [data-testid='job-title'] a")
                            co_el = await card.query_selector(".company-name, [data-testid='company-name']")
                            lo_el = await card.query_selector(".location, [data-testid='job-location']")

                            title    = (await t_el.inner_text()).strip()  if t_el  else ""
                            company  = (await co_el.inner_text()).strip() if co_el else ""
                            location = (await lo_el.inner_text()).strip() if lo_el else ""
                            href     = await t_el.get_attribute("href")   if t_el  else ""

                            if title and href and href not in seen:
                                seen.add(href)
                                full_url = href if href.startswith("http") else f"https://builtin.com{href}"
                                results.append({
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "description": f"{title} at {company} ({location})",
                                    "url": full_url,
                                    "source": "builtin",
                                })
                        except Exception:
                            continue

                    if len(results) >= 30:
                        break
                except Exception as e:
                    print(f"[builtin] query error: {e}")

            await browser.close()
    except Exception as e:
        print(f"[builtin] Error: {e}")

    print(f"[builtin] {len(results)} jobs found")
    return results
