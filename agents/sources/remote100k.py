import urllib.parse
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


async def remote100k_source(queries: list[str], country: str = "") -> list[dict]:
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
                    url = f"https://remote100k.com/jobs?q={q}"
                    await page.goto(url, timeout=25000)
                    await page.wait_for_timeout(2500)

                    cards = await page.query_selector_all(".job, .job-card, [class*='job-listing'], article")
                    if not cards:
                        # Try the general jobs listing (no query filter — browse mode)
                        await page.goto("https://remote100k.com/jobs", timeout=25000)
                        await page.wait_for_timeout(2500)
                        cards = await page.query_selector_all(".job, .job-card, article, li[class*='job']")

                    for card in cards:
                        try:
                            t_el  = await card.query_selector("h2 a, h3 a, a[class*='title'], .job-title a")
                            co_el = await card.query_selector(".company, .company-name, span[class*='company']")
                            lo_el = await card.query_selector(".location, span[class*='location']")
                            sa_el = await card.query_selector(".salary, span[class*='salary']")

                            title    = (await t_el.inner_text()).strip()  if t_el  else ""
                            company  = (await co_el.inner_text()).strip() if co_el else ""
                            location = (await lo_el.inner_text()).strip() if lo_el else "Remote"
                            salary   = (await sa_el.inner_text()).strip() if sa_el else ""
                            href     = await t_el.get_attribute("href")   if t_el  else ""

                            if title and href and href not in seen:
                                seen.add(href)
                                full_url = href if href.startswith("http") else f"https://remote100k.com{href}"
                                desc = f"{title} at {company}"
                                if salary:
                                    desc += f" | {salary}"
                                results.append({
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "description": desc,
                                    "url": full_url,
                                    "source": "remote100k",
                                })
                        except Exception:
                            continue

                    if len(results) >= 20:
                        break
                except Exception as e:
                    print(f"[remote100k] query error: {e}")

            await browser.close()
    except Exception as e:
        print(f"[remote100k] Error: {e}")

    print(f"[remote100k] {len(results)} jobs found")
    return results
