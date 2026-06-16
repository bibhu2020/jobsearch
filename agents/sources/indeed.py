import urllib.parse
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


async def indeed_source(queries: list[str]) -> list[dict]:
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
                    url = f"https://www.indeed.com/jobs?q={q}&l=remote&sort=date&fromage=14"
                    await page.goto(url, timeout=25000)
                    await page.wait_for_timeout(2000)

                    for card in await page.query_selector_all('.job_seen_beacon'):
                        try:
                            # Title: span inside the job title link
                            title_el   = await card.query_selector('.jobTitle a span')
                            company_el = await card.query_selector('[data-testid="company-name"]')
                            loc_el     = await card.query_selector('[data-testid="text-location"]')
                            link_el    = await card.query_selector('a[data-jk]')

                            title    = (await title_el.inner_text()).strip()   if title_el   else ""
                            company  = (await company_el.inner_text()).strip() if company_el else ""
                            location = (await loc_el.inner_text()).strip()     if loc_el     else ""
                            jk       = await link_el.get_attribute('data-jk') if link_el    else ""
                            job_url  = f"https://www.indeed.com/viewjob?jk={jk}" if jk else ""

                            if title and job_url and job_url not in seen:
                                seen.add(job_url)
                                results.append({
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "description": f"{title} at {company} ({location})",
                                    "url": job_url,
                                    "source": "indeed",
                                })
                        except Exception:
                            continue

                    if len(results) >= 25:
                        break
                except Exception as e:
                    print(f"[indeed] query error: {e}")

            await browser.close()
    except Exception as e:
        print(f"[indeed] Error: {e}")

    print(f"[indeed] {len(results)} jobs found")
    return results
