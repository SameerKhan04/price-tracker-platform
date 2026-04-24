"""
scraper/factory.py
------------------
Returns the correct scraper for a given URL.

Why a factory?
Adding a new site-specific scraper (e.g. eBay, Kogan) means:
  1. Create app/scraper/ebay.py with class EbayScraper(AbstractScraper)
  2. Add "ebay.com" -> EbayScraper to SCRAPER_REGISTRY below
That's it. No other code changes needed.
"""

import logging
from urllib.parse import urlparse

from app.scraper.base import AbstractScraper
from app.scraper.generic import GenericScraper

logger = logging.getLogger(__name__)

# Registry: domain substring -> scraper class
# More specific entries should come first.
SCRAPER_REGISTRY: dict[str, type[AbstractScraper]] = {
    # Site-specific scrapers can be added here as the project grows.
    # "amazon.com": AmazonScraper,
    # "ebay.com":   EbayScraper,
    # "kogan.com":  KoganScraper,
}


def get_scraper(url: str) -> AbstractScraper:
    """
    Return an instantiated scraper appropriate for the given URL.
    Falls back to GenericScraper if no site-specific scraper is registered.
    """
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        logger.warning(f"Could not parse domain from URL: {url!r}")
        return GenericScraper()

    for registered_domain, scraper_class in SCRAPER_REGISTRY.items():
        if registered_domain in domain:
            logger.debug(f"Using {scraper_class.__name__} for {domain}")
            return scraper_class()

    logger.debug(f"No specific scraper for {domain!r}, using GenericScraper")
    return GenericScraper()