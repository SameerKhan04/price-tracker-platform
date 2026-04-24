"""
scraper/base.py
---------------
Abstract base class for all scrapers.

Why use an abstract base class?
The ScraperFactory returns whichever scraper matches the URL's domain.
Each scraper must implement scrape() and return a ScrapeResult.
Adding support for a new site means creating one new class that
inherits from AbstractScraper — nothing else changes.

This is the Open/Closed Principle: open for extension, closed for modification.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScrapeResult:
    """
    Structured result returned by every scraper.
    Using a dataclass instead of a dict makes the contract explicit —
    callers know exactly what fields to expect.
    """
    url: str
    title: Optional[str]
    price: Optional[float]
    currency: str
    image_url: Optional[str]
    source_site: str
    success: bool
    error: Optional[str] = None


class AbstractScraper(ABC):
    """
    Every scraper must implement scrape().
    Subclasses can override _get_headers() to provide
    site-specific User-Agent strings or cookies.
    """

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def _get_headers(self) -> dict:
        return self.DEFAULT_HEADERS.copy()

    @abstractmethod
    def scrape(self, url: str, timeout: int = 10) -> ScrapeResult:
        """
        Fetch the page at `url` and extract product metadata.
        Must always return a ScrapeResult — never raise exceptions.
        On failure, return ScrapeResult(success=False, error="reason").
        """
        raise NotImplementedError