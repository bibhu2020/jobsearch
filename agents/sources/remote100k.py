from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

STOPWORDS = {"remote", "jobs", "job", "senior", "junior", "the", "and", "worldwide"}


async def remote100k_source(queries: list[str], country: str = "") -> list[dict]:
    results = []
    seen = set()
    # Remote100k has no keyword-search URL — pull the engineering listing and filter client-side.
    keywords = {w.lower() for q in queries for w in q.split() if len(w) > 3 and w.lower() not in STOPWORDS}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 900})
            page = await ctx.new_page()

            await page.goto("https://remote100k.com/remote-jobs/engineering", timeout=25000)
            await page.wait_for_timeout(3000)

            cards = await page.query_selector_all("a.job-card")
            for card in cards:
                try:
                    t_el  = await card.query_selector(".job-card-desktop-title")
                    co_el = await card.query_selector(".job-card-desktop-company")
                    lo_el = await card.query_selector(".job-card-desktop-body .job-card-meta span")

                    title    = (await t_el.inner_text()).strip()  if t_el  else ""
                    company  = (await co_el.inner_text()).strip() if co_el else ""
                    location = (await lo_el.inner_text()).strip() if lo_el else "Remote"
                    href     = await card.get_attribute("href")

                    if not title or not href or href in seen:
                        continue

                    job_text = f"{title} {company}".lower()
                    if keywords and not any(kw in job_text for kw in keywords):
                        continue

                    seen.add(href)
                    full_url = href if href.startswith("http") else f"https://remote100k.com{href}"
                    results.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": f"{title} at {company}",
                        "url": full_url,
                        "source": "remote100k",
                    })
                except Exception:
                    continue

                if len(results) >= 20:
                    break

            await browser.close()
    except Exception as e:
        print(f"[remote100k] Error: {e}")

    print(f"[remote100k] {len(results)} jobs found")
    return results
