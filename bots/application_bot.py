"""
Job Application Bot — Playwright-based automation for LinkedIn, Indeed, Handshake, and generic company sites.

Flow:
1. User provides job search criteria (titles, location, optional URLs)
2. Bot scrapes matching listings from supported platforms
3. Claude scores each listing's fit against the user's profile
4. For each matched role: bot presents it to user for confirmation, then auto-applies

Note: Users must provide login credentials in .env for each platform they want to use.
"""

import os
import json
import asyncio
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

# Rate limiting — pause between actions to avoid detection
ACTION_DELAY = 2.0  # seconds between page interactions


async def search_linkedin(page, job_title: str, location: str) -> list[dict]:
    """Scrape LinkedIn Easy Apply listings."""
    listings = []
    try:
        search_url = (
            f"https://www.linkedin.com/jobs/search/?keywords={job_title.replace(' ', '%20')}"
            f"&location={location.replace(' ', '%20')}&f_AL=true"
        )
        await page.goto(search_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(ACTION_DELAY)

        job_cards = await page.query_selector_all(".job-search-card")
        for card in job_cards[:10]:
            try:
                title = await card.query_selector(".job-search-card__title")
                company = await card.query_selector(".job-search-card__subtitle")
                link = await card.query_selector("a.job-search-card__title-link")
                listings.append({
                    "title": await title.inner_text() if title else "",
                    "company": await company.inner_text() if company else "",
                    "url": await link.get_attribute("href") if link else "",
                    "platform": "linkedin",
                })
            except Exception:
                continue
    except Exception as e:
        print(f"LinkedIn search error: {e}")
    return listings


async def search_indeed(page, job_title: str, location: str) -> list[dict]:
    """Scrape Indeed listings."""
    listings = []
    try:
        search_url = (
            f"https://www.indeed.com/jobs?q={job_title.replace(' ', '+')}"
            f"&l={location.replace(' ', '+')}"
        )
        await page.goto(search_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(ACTION_DELAY)

        job_cards = await page.query_selector_all(".job_seen_beacon")
        for card in job_cards[:10]:
            try:
                title_el = await card.query_selector("h2.jobTitle span")
                company_el = await card.query_selector("[data-testid='company-name']")
                link_el = await card.query_selector("h2.jobTitle a")
                href = await link_el.get_attribute("href") if link_el else ""
                listings.append({
                    "title": await title_el.inner_text() if title_el else "",
                    "company": await company_el.inner_text() if company_el else "",
                    "url": f"https://www.indeed.com{href}" if href.startswith("/") else href,
                    "platform": "indeed",
                })
            except Exception:
                continue
    except Exception as e:
        print(f"Indeed search error: {e}")
    return listings


async def search_handshake(page, job_title: str, location: str) -> list[dict]:
    """Scrape Handshake listings (requires login)."""
    listings = []
    try:
        search_url = (
            f"https://app.joinhandshake.com/jobs?query={job_title.replace(' ', '%20')}"
            f"&location={location.replace(' ', '%20')}"
        )
        await page.goto(search_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(ACTION_DELAY)

        job_cards = await page.query_selector_all("[data-hook='job-card']")
        for card in job_cards[:10]:
            try:
                title_el = await card.query_selector("[data-hook='job-card-title']")
                company_el = await card.query_selector("[data-hook='job-card-employer-name']")
                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                listings.append({
                    "title": await title_el.inner_text() if title_el else "",
                    "company": await company_el.inner_text() if company_el else "",
                    "url": f"https://app.joinhandshake.com{href}" if href.startswith("/") else href,
                    "platform": "handshake",
                })
            except Exception:
                continue
    except Exception as e:
        print(f"Handshake search error: {e}")
    return listings


def score_job_fit(listing: dict, user_profile: dict) -> dict:
    """Ask Claude to score how well this job fits the user's profile."""
    prompt = f"""Rate how well this job matches this candidate. Reply with JSON only.

Job: {listing['title']} at {listing['company']}

Candidate:
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}
- Target roles: {', '.join(user_profile.get('target_roles', []))}
- Degree: {user_profile.get('degree', '')}

Reply with this exact JSON:
{{"score": <1-10>, "reason": "<one sentence>", "apply": <true|false>}}

apply=true if score >= 6."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        text = response.content[0].text.strip()
        # Extract JSON if wrapped in markdown
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except Exception:
        return {"score": 5, "reason": "Could not assess fit", "apply": False}


async def apply_linkedin(page, url: str, user_profile: dict) -> bool:
    """Attempt LinkedIn Easy Apply."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(ACTION_DELAY)

        apply_btn = await page.query_selector(".jobs-apply-button")
        if not apply_btn:
            return False
        await apply_btn.click()
        await asyncio.sleep(ACTION_DELAY)

        # Fill in common fields
        await _fill_common_fields(page, user_profile)

        # Submit
        submit_btn = await page.query_selector("button[aria-label='Submit application']")
        if submit_btn:
            await submit_btn.click()
            await asyncio.sleep(ACTION_DELAY)
            return True
    except Exception as e:
        print(f"LinkedIn apply error: {e}")
    return False


async def apply_generic(page, url: str, user_profile: dict) -> bool:
    """Generic form-fill for company career pages using Claude to identify fields."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(ACTION_DELAY)
        await _fill_common_fields(page, user_profile)
        return True
    except Exception as e:
        print(f"Generic apply error: {e}")
    return False


async def _fill_common_fields(page, user_profile: dict):
    """Fill common application form fields using user profile data."""
    field_map = {
        "input[name*='first'], input[placeholder*='First name' i]": user_profile.get("name", "").split()[0],
        "input[name*='last'], input[placeholder*='Last name' i]": (user_profile.get("name", "").split() or [""])[-1],
        "input[type='email'], input[name*='email']": user_profile.get("email", ""),
        "input[name*='university'], input[placeholder*='University' i], input[placeholder*='School' i]": user_profile.get("university", ""),
        "input[name*='degree'], input[placeholder*='Degree' i]": user_profile.get("degree", ""),
    }
    for selector, value in field_map.items():
        if not value:
            continue
        try:
            el = await page.query_selector(selector)
            if el:
                await el.fill(str(value))
                await asyncio.sleep(0.3)
        except Exception:
            continue


async def run_application_session(
    job_titles: list[str],
    location: str,
    user_profile: dict,
    on_confirm,  # async callback: (listing, fit) -> bool
    on_status,   # async callback: (listing, status) -> None
):
    """
    Main entry point for the application bot.
    Searches all platforms, scores fit, confirms with user, and applies.
    """
    from playwright.async_api import async_playwright

    all_listings = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        for job_title in job_titles:
            linkedin = await search_linkedin(page, job_title, location)
            indeed = await search_indeed(page, job_title, location)
            handshake = await search_handshake(page, job_title, location)
            all_listings.extend(linkedin + indeed + handshake)

        # Deduplicate by URL
        seen = set()
        unique_listings = []
        for l in all_listings:
            if l["url"] and l["url"] not in seen:
                seen.add(l["url"])
                unique_listings.append(l)

        for listing in unique_listings:
            fit = score_job_fit(listing, user_profile)
            if not fit.get("apply"):
                await on_status(listing, "skipped (low fit)")
                continue

            confirmed = await on_confirm(listing, fit)
            if not confirmed:
                await on_status(listing, "skipped (user declined)")
                continue

            platform = listing.get("platform", "generic")
            if platform == "linkedin":
                success = await apply_linkedin(page, listing["url"], user_profile)
            else:
                success = await apply_generic(page, listing["url"], user_profile)

            status = "applied" if success else "failed"
            await on_status(listing, status)
            await asyncio.sleep(ACTION_DELAY)

        await browser.close()

    return unique_listings
