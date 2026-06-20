"""Playwright-based conference attendee directory scraper.

Uses a headless Chromium browser (via Playwright) to scrape attendee/speaker
lists from conference websites.  Supports:
  - Generic conference directory pages (heuristic extraction)
  - lu.ma public event pages (structured selectors)

The scraper returns normalised attendee dicts ready for the pre-meet pipeline::

    {
        "name":           str | None,
        "email":          str | None,
        "title":          str | None,
        "company":        str | None,
        "company_domain": str | None,
        "linkedin":       str | None,
        "bio":            str | None,
        "interests":      list[str],
        "source":         "playwright",
    }

Dependencies: playwright (``pip install playwright && playwright install chromium``)
"""

from __future__ import annotations

import re
import asyncio
from typing import Optional, Any
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Playwright import guard — Playwright is an optional dep.
# ---------------------------------------------------------------------------
try:
    from playwright.async_api import async_playwright, Page, Browser
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PLAYWRIGHT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Heuristic helpers
# ---------------------------------------------------------------------------

_PERSONAL_DOMAINS = frozenset([
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "icloud.com", "protonmail.com", "me.com", "live.com",
])

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+/?")


def _domain_from_email(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    domain = email.split("@")[-1].lower()
    return None if domain in _PERSONAL_DOMAINS else domain


def _extract_emails(text: str) -> list[str]:
    return _EMAIL_RE.findall(text)


def _extract_linkedin(text: str) -> Optional[str]:
    m = _LINKEDIN_RE.search(text)
    return m.group(0) if m else None


# ---------------------------------------------------------------------------
# Luma-specific selectors
# ---------------------------------------------------------------------------

class _LumaScraper:
    """Scrape a public lu.ma event page for visible attendee cards."""

    # Luma renders attendee cards with these CSS classes (as of mid-2025)
    GUEST_CARD_SEL = "[data-testid='guest-card'], .guest-card, .attendee-card"
    NAME_SEL = ".guest-name, [data-testid='guest-name'], h3, h4"
    HEADLINE_SEL = ".guest-headline, [data-testid='guest-headline'], .subtitle"

    async def scrape(self, page: "Page", url: str) -> list[dict[str, Any]]:
        await page.goto(url, wait_until="networkidle", timeout=45_000)

        # Scroll to load lazy-rendered attendees
        for _ in range(6):
            await page.keyboard.press("End")
            await asyncio.sleep(1.0)

        attendees: list[dict[str, Any]] = []
        cards = await page.query_selector_all(self.GUEST_CARD_SEL)

        if not cards:
            # Fall back to generic heuristic scraping
            return await _GenericScraper().scrape(page, url)

        for card in cards:
            text = await card.inner_text()
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            name = lines[0] if lines else None
            headline = lines[1] if len(lines) > 1 else None
            title, company = _split_headline(headline)
            linkedin = _extract_linkedin(await card.inner_html())

            attendees.append({
                "name": name,
                "email": None,
                "title": title,
                "company": company,
                "company_domain": None,
                "linkedin": linkedin,
                "bio": None,
                "interests": [],
                "source": "playwright:luma",
            })

        return attendees


class _GenericScraper:
    """Heuristic scraper for arbitrary conference directory pages.

    Strategy:
      1. Find all <a> tags containing 'linkedin.com/in/' → person profiles
      2. Walk parent containers to extract name/title/company text
      3. Supplement with any visible email addresses in the page
    """

    async def scrape(self, page: "Page", url: str) -> list[dict[str, Any]]:
        await page.goto(url, wait_until="networkidle", timeout=45_000)

        # Scroll to trigger lazy-load
        for _ in range(8):
            await page.keyboard.press("End")
            await asyncio.sleep(0.8)

        attendees: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        # Strategy A: LinkedIn profile links → person cards
        linkedin_links = await page.query_selector_all("a[href*='linkedin.com/in/']")
        for link in linkedin_links:
            href = await link.get_attribute("href") or ""
            linkedin = _LINKEDIN_RE.search(href)
            linkedin_url = linkedin.group(0) if linkedin else href

            # Walk up to a reasonable parent container
            parent = await link.evaluate_handle(
                "(el) => el.closest('li') || el.closest('article') "
                "|| el.closest('[class*=card]') || el.closest('[class*=member]') "
                "|| el.closest('[class*=speaker]') || el.closest('[class*=attendee]') "
                "|| el.parentElement"
            )
            text = await parent.evaluate("(el) => el ? el.innerText : ''")
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            name = lines[0] if lines else None
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            headline = lines[1] if len(lines) > 1 else None
            title, company = _split_headline(headline)
            emails = _extract_emails(text)
            email = emails[0] if emails else None

            attendees.append({
                "name": name,
                "email": email,
                "title": title,
                "company": company,
                "company_domain": _domain_from_email(email),
                "linkedin": linkedin_url,
                "bio": " ".join(lines[2:]) if len(lines) > 2 else None,
                "interests": [],
                "source": "playwright:generic",
            })

        # Strategy B: structured speaker/attendee grid elements
        if not attendees:
            card_sel = (
                "[class*='speaker'], [class*='attendee'], [class*='member'], "
                "[class*='profile'], [class*='person']"
            )
            cards = await page.query_selector_all(card_sel)
            for card in cards:
                text = await card.inner_text()
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                name = lines[0] if lines else None
                if not name or name in seen_names or len(name) > 60:
                    continue
                seen_names.add(name)
                headline = lines[1] if len(lines) > 1 else None
                title, company = _split_headline(headline)
                card_html = await card.inner_html()
                linkedin = _extract_linkedin(card_html)
                emails = _extract_emails(text)
                email = emails[0] if emails else None
                attendees.append({
                    "name": name,
                    "email": email,
                    "title": title,
                    "company": company,
                    "company_domain": _domain_from_email(email),
                    "linkedin": linkedin,
                    "bio": " ".join(lines[2:]) if len(lines) > 2 else None,
                    "interests": [],
                    "source": "playwright:generic",
                })

        return attendees


# ---------------------------------------------------------------------------
# Headline splitter
# ---------------------------------------------------------------------------

def _split_headline(headline: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Split 'VP of Sales @ Acme Corp' → ('VP of Sales', 'Acme Corp')."""
    if not headline:
        return None, None
    for sep in (" @ ", " at ", " | ", " — ", " - ", ", "):
        if sep in headline:
            parts = headline.split(sep, 1)
            return parts[0].strip() or None, parts[1].strip() or None
    return headline.strip() or None, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ConferenceDirectoryScraper:
    """Playwright-based conference attendee / speaker directory scraper.

    Args:
        headless:  Run browser headlessly (default True).
        slow_mo:   Slow down Playwright operations by given ms (useful for debug).

    Usage::

        scraper = ConferenceDirectoryScraper()
        attendees = await scraper.scrape("https://lu.ma/ai-hackathon-sf")
    """

    def __init__(self, headless: bool = True, slow_mo: int = 0):
        if not _PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "playwright is required: pip install playwright && playwright install chromium"
            )
        self.headless = headless
        self.slow_mo = slow_mo

    async def scrape(
        self,
        url: str,
        *,
        max_attendees: int = 500,
    ) -> list[dict[str, Any]]:
        """Scrape attendees from the given conference directory URL.

        Automatically selects luma-specific or generic extraction based on the
        hostname.

        Returns a list of normalised attendee dicts (see module docstring).
        """
        async with async_playwright() as pw:
            browser: Browser = await pw.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            host = urlparse(url).hostname or ""
            if "lu.ma" in host or "luma" in host:
                impl = _LumaScraper()
            else:
                impl = _GenericScraper()

            try:
                attendees = await impl.scrape(page, url)
            except Exception as exc:
                print(f"ConferenceDirectoryScraper error for {url}: {exc}")
                attendees = []
            finally:
                await browser.close()

        return attendees[:max_attendees]

    async def scrape_multiple(
        self,
        urls: list[str],
        *,
        max_attendees: int = 500,
    ) -> list[dict[str, Any]]:
        """Scrape multiple directory pages and deduplicate by name."""
        all_attendees: list[dict[str, Any]] = []
        seen: set[str] = set()
        for url in urls:
            for att in await self.scrape(url, max_attendees=max_attendees):
                key = (att.get("name") or "").lower().strip()
                if key and key not in seen:
                    seen.add(key)
                    all_attendees.append(att)
        return all_attendees[:max_attendees]
