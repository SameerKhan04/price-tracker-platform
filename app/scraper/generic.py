"""
scraper/generic.py
------------------
A heuristic scraper that works on most e-commerce sites
without site-specific selectors.

Strategy:
1. Try structured data first (JSON-LD schema.org/Product) — most
   modern e-commerce sites include this and it's highly reliable.
2. Fall back to Open Graph meta tags (og:title, og:price, og:image).
3. Fall back to common CSS selector patterns for price elements.

NOTE on rate limiting and ethics:
- We add a configurable SCRAPER_DELAY between requests (default 2s).
- We send a real browser User-Agent to identify ourselves.
- We do NOT bypass CAPTCHAs or authentication.
- Production use should also check robots.txt via urllib.robotparser.
- See README for full ethical scraping policy.
"""

import json
import logging
import re
from typing import Optional
from urllib.parse import urlparse

import requests
from app.scraper.base import AbstractScraper, ScrapeResult
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Common CSS selectors for price elements across e-commerce sites.
# Ordered from most specific to least specific.
PRICE_SELECTORS = [
    "[itemprop='price']",
    ".price",
    ".product-price",
    ".offer-price",
    "#priceblock_ourprice",   # Amazon legacy
    "#corePriceDisplay_desktop_feature_div .a-price-whole",
    ".a-price .a-offscreen",  # Amazon
    "[data-testid='price']",
    ".price-tag",
    ".sale-price",
    ".current-price",
    "span.price",
]


def _extract_price(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = text.strip()
    # European format: 1.299,99 (dot=thousands, comma=decimal)
    if re.search(r'\d{1,3}(\.\d{3})+,\d{2}', cleaned):
        cleaned = cleaned.replace('.', '').replace(',', '.')
    else:
        cleaned = cleaned.replace(',', '')
    cleaned = re.sub(r'[^\d.]', '', cleaned)
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None


class GenericScraper(AbstractScraper):
    """
    Heuristic scraper using BeautifulSoup.
    Works on most e-commerce sites without configuration.
    """

    def scrape(self, url: str, timeout: int = 10) -> ScrapeResult:
        source_site = urlparse(url).netloc.replace("www.", "")

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout scraping {url}")
            return ScrapeResult(
                url=url, title=None, price=None, currency="AUD",
                image_url=None, source_site=source_site,
                success=False, error="Request timed out"
            )
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP {e.response.status_code} scraping {url}")
            return ScrapeResult(
                url=url, title=None, price=None, currency="AUD",
                image_url=None, source_site=source_site,
                success=False, error=f"HTTP error: {e.response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return ScrapeResult(
                url=url, title=None, price=None, currency="AUD",
                image_url=None, source_site=source_site,
                success=False, error=str(e)
            )

        soup = BeautifulSoup(response.text, "html.parser")
        title, price, image_url, currency = None, None, None, "AUD"

        # ── Strategy 1: JSON-LD structured data ──────────────────────
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                # Handle both single object and @graph array
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") in ("Product", "IndividualProduct"):
                        title = title or item.get("name")
                        image_url = image_url or (
                            item.get("image") if isinstance(item.get("image"), str)
                            else (item.get("image") or [None])[0]
                        )
                        offers = item.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        price = price or _extract_price(str(offers.get("price", "")))
                        currency = offers.get("priceCurrency", "AUD")
                        if title and price:
                            break
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue

        # ── Strategy 2: Open Graph meta tags ─────────────────────────
        if not title:
            og_title = soup.find("meta", property="og:title")
            title = og_title["content"] if og_title and og_title.get("content") else None

        if not image_url:
            og_image = soup.find("meta", property="og:image")
            image_url = og_image["content"] if og_image and og_image.get("content") else None

        if not price:
            og_price = soup.find("meta", property="product:price:amount")
            if not og_price:
                og_price = soup.find("meta", property="og:price:amount")
            if og_price and og_price.get("content"):
                price = _extract_price(og_price["content"])

        # ── Strategy 3: CSS selector fallbacks ───────────────────────
        if not title:
            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else None

        if not price:
            for selector in PRICE_SELECTORS:
                el = soup.select_one(selector)
                if el:
                    candidate = _extract_price(el.get_text(strip=True) or el.get("content", ""))
                    if candidate and 0.01 <= candidate <= 1_000_000:
                        price = candidate
                        break

        # Truncate title to prevent DB overflow
        if title:
            title = title[:490]

        success = price is not None
        error = None if success else "Could not extract price from page"

        logger.info(
            f"Scraped {source_site}: title={title!r}, price={price}, success={success}"
        )

        return ScrapeResult(
            url=url,
            title=title,
            price=price,
            currency=currency,
            image_url=image_url,
            source_site=source_site,
            success=success,
            error=error,
        )