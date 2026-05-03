"""
tests/test_scraper.py
---------------------
Tests for the scraper layer.

We mock HTTP responses so tests run offline and don't hit real websites.
"""

from unittest.mock import MagicMock, patch

import pytest
from app.scraper.generic import GenericScraper, _extract_price
from app.scraper.factory import get_scraper


# ── _extract_price unit tests ─────────────────────────────────────────────────

class TestExtractPrice:
    def test_simple_dollar(self):
        assert _extract_price("$49.99") == 49.99

    def test_with_currency_code(self):
        assert _extract_price("AUD 1,299.00") == 1299.00

    def test_no_decimal(self):
        assert _extract_price("$32") == 32.0

    def test_european_format(self):
        assert _extract_price("1.299,99") == 1299.99

    def test_comma_thousands(self):
        assert _extract_price("$1,299.99") == 1299.99

    def test_empty_string(self):
        assert _extract_price("") is None

    def test_none_input(self):
        assert _extract_price(None) is None

    def test_non_numeric(self):
        assert _extract_price("Out of stock") is None

    def test_price_with_spaces(self):
        assert _extract_price("  $  99.95  ") == 99.95


# ── get_scraper factory tests ─────────────────────────────────────────────────

class TestScraperFactory:
    def test_unknown_domain_returns_generic(self):
        from app.scraper.generic import GenericScraper
        scraper = get_scraper("https://www.somesite.com.au/product/123")
        assert isinstance(scraper, GenericScraper)

    def test_invalid_url_returns_generic(self):
        from app.scraper.generic import GenericScraper
        scraper = get_scraper("not-a-url")
        assert isinstance(scraper, GenericScraper)


# ── GenericScraper integration tests (mocked HTTP) ────────────────────────────

MOCK_HTML_JSON_LD = """
<html>
<head>
  <script type="application/ld+json">
  {
    "@type": "Product",
    "name": "Test Headphones",
    "image": "https://example.com/img.jpg",
    "offers": {
      "@type": "Offer",
      "price": "79.99",
      "priceCurrency": "AUD"
    }
  }
  </script>
</head>
<body><h1>Test Headphones</h1></body>
</html>
"""

MOCK_HTML_OG_TAGS = """
<html>
<head>
  <meta property="og:title" content="Blue Wireless Headphones" />
  <meta property="og:image" content="https://example.com/headphones.jpg" />
  <meta property="product:price:amount" content="59.95" />
</head>
<body><h1>Blue Wireless Headphones</h1></body>
</html>
"""

MOCK_HTML_CSS_SELECTOR = """
<html>
<body>
  <h1>Mechanical Keyboard</h1>
  <span class="price">$129.00</span>
</body>
</html>
"""

MOCK_HTML_NO_PRICE = """
<html>
<body>
  <h1>Some Product</h1>
  <p>Price not available</p>
</body>
</html>
"""


def _mock_response(html, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


class TestGenericScraper:
    def setup_method(self):
        self.scraper = GenericScraper()
        self.url = "https://www.example.com.au/product/123"

    @patch("app.scraper.generic.requests.get")
    def test_json_ld_extraction(self, mock_get):
        mock_get.return_value = _mock_response(MOCK_HTML_JSON_LD)
        result = self.scraper.scrape(self.url)
        assert result.success is True
        assert result.price == 79.99
        assert result.title == "Test Headphones"
        assert result.currency == "AUD"

    @patch("app.scraper.generic.requests.get")
    def test_og_tag_extraction(self, mock_get):
        mock_get.return_value = _mock_response(MOCK_HTML_OG_TAGS)
        result = self.scraper.scrape(self.url)
        assert result.success is True
        assert result.price == 59.95
        assert result.title == "Blue Wireless Headphones"

    @patch("app.scraper.generic.requests.get")
    def test_css_selector_fallback(self, mock_get):
        mock_get.return_value = _mock_response(MOCK_HTML_CSS_SELECTOR)
        result = self.scraper.scrape(self.url)
        assert result.success is True
        assert result.price == 129.00
        assert result.title == "Mechanical Keyboard"

    @patch("app.scraper.generic.requests.get")
    def test_no_price_returns_failure(self, mock_get):
        mock_get.return_value = _mock_response(MOCK_HTML_NO_PRICE)
        result = self.scraper.scrape(self.url)
        assert result.success is False
        assert result.price is None
        assert result.error == "Could not extract price from page"

    @patch("app.scraper.generic.requests.get")
    def test_http_403_returns_failure(self, mock_get):
        import requests as req
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_get.return_value = mock_resp
        mock_resp.raise_for_status.side_effect = req.exceptions.HTTPError(
            response=mock_resp
        )
        result = self.scraper.scrape(self.url)
        assert result.success is False
        assert "403" in result.error

    @patch("app.scraper.generic.requests.get")
    def test_timeout_returns_failure(self, mock_get):
        import requests as req
        mock_get.side_effect = req.exceptions.Timeout()
        result = self.scraper.scrape(self.url)
        assert result.success is False
        assert "timed out" in result.error.lower()