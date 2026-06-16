import urllib.parse
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


async def remoterocketship_source(queries: list[str], country: str = "") -> list[dict]:
    results = []
    seen = set()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 900})
            page = await ctx.new_page()

            for query in queries[:2]:
                try:
                    q = urllib.parse.quote_plus(query)
                    url = f"https://remoterocketship.com/jobs?search={q}"
                    await page.goto(url, timeout=25000)
                    await page.wait_for_timeout(2500)

                    cards = await page.query_selector_all(
                        "tr[class*='job'], .job-row, [class*='JobRow'], "
                        "li[class*='job'], div[class*='job-card'], article"
                    )

                    for card in cards:
                        try:
                            t_el  = await card.query_selector("a[href*='/jobs/'], a[class*='title'], h2 a, h3 a")
                            co_el = await card.query_selector("[class*='company'], td:nth-child(2)")
                            lo_el = await card.query_selector("[class*='location'], td[class*='loc']")

                            title    = (await t_el.inner_text()).strip()  if t_el  else ""
                            company  = (await co_el.inner_text()).strip() if co_el else ""
                            location = (await lo_el.inner_text()).strip() if lo_el else "Remote"
                            href     = await t_el.get_attribute("href")   if t_el  else ""

                            if title and href and href not in seen:
                                seen.add(href)
                                full_url = href if href.startswith("http") else f"https://remoterocketship.com{href}"
                                results.append({
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "description": f"{title} at {company}",
                                    "url": full_url,
                                    "source": "remoterocketship",
                                })
                        except Exception:
                            continue

                    if len(results) >= 20:
                        break
                except Exception as e:
                    print(f"[remoterocketship] query error: {e}")

            await browser.close()
    except Exception as e:
        print(f"[remoterocketship] Error: {e}")

    print(f"[remoterocketship] {len(results)} jobs found")
    return results
