# Price Tracker Platform

A production-style full-stack price tracking web application built with Flask, PostgreSQL, Celery, and Redis. Users can track product prices from e-commerce sites, view historical price charts, and receive in-app alerts when prices drop.

Built as a portfolio project demonstrating real engineering practices: service layers, background job scheduling, scraper abstraction, role-based access control, and a full test suite with CI.

---

## Screenshots


---

## Features

- **User authentication** — register, login, logout with bcrypt password hashing
- **Product tracking** — add any product URL; metadata (title, price, image) scraped automatically
- **Price history charts** — interactive Chart.js line charts showing price over time
- **In-app notifications** — notified when a tracked product drops below your alert price
- **Background scraping** — Celery Beat refreshes all tracked products every 60 minutes
- **Retry logic** — failed scrape tasks retry with exponential backoff (max 3 attempts)
- **Admin panel** — view scrape job audit log, manage users and products, trigger manual scrapes
- **Role-based access** — admin routes protected by `is_admin` flag, not just login
- **Global error pages** — friendly 404 and 500 HTML responses
- **Rate limiting** — login endpoint protected against brute-force attempts
- **Structured logging** — all key events logged with Python's `logging` module

---

## Architecture

```
Users (Browser)
     │
     ▼ HTTP
┌─────────────────────────────────────┐
│         Flask Web Application       │
│  auth │ products │ dashboard │ admin │
│         Services Layer              │
│  AuthService │ ProductService       │
│  PriceService │ NotificationService │
│         SQLAlchemy ORM              │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
  PostgreSQL          Redis
  (persistent)      (broker)
                        │
              ┌─────────┴──────────┐
              ▼                    ▼
        Celery Worker         Celery Beat
        (scrape tasks)        (60min schedule)
```

**Request flow for price tracking:**
1. User submits a URL → Flask validates input → `ProductService` creates a DB record → Celery task queued
2. Celery Worker runs `scrape_product` → calls `ScraperFactory` → stores price in `PriceHistory` → creates `Notification` if price dropped
3. Celery Beat fires `refresh_all_products` every 60 minutes → re-queues one scrape task per active product
4. User visits dashboard → Flask renders Jinja2 templates → Chart.js draws interactive price charts

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Flask 3.0 |
| Database | PostgreSQL + SQLAlchemy + Flask-Migrate |
| Background jobs | Celery 5 + Redis |
| Scraping | requests + BeautifulSoup4 |
| Authentication | Flask-Login + bcrypt |
| Charts | Chart.js 4 |
| Containerisation | Docker + Docker Compose |
| Testing | pytest + pytest-cov |
| CI | GitHub Actions |

---

## Project Structure

```
price-tracker-platform/
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── extensions.py        # db, login_manager, celery singletons
│   ├── config.py            # Base, Dev, Test, Prod config classes
│   ├── auth/                # Register, login, logout blueprint
│   ├── products/            # Add/remove tracked products blueprint
│   ├── dashboard/           # Watchlist, charts, notifications blueprint
│   ├── admin/               # Admin panel blueprint (is_admin required)
│   ├── models/              # SQLAlchemy models (one file per entity)
│   ├── services/            # Business logic, decoupled from HTTP
│   ├── scraper/             # Scraper abstraction (Factory + GenericScraper)
│   ├── tasks/               # Celery tasks (scrape, alert)
│   └── templates/           # Jinja2 templates + error pages
├── tests/
│   ├── conftest.py          # Fixtures: test app, test DB, test client
│   ├── test_auth.py         # Register, login, logout flows
│   ├── test_products.py     # Add/remove product routes
│   ├── test_services.py     # PriceService, NotificationService unit tests
│   └── test_tasks.py        # Celery task logic (mocked scraper)
├── migrations/              # Flask-Migrate / Alembic migration files
├── docker/
│   └── celery-entrypoint.sh # Worker vs beat startup script
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions: lint + test on push/PR
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── celeryworker.py
├── wsgi.py
└── README.md
```

---

## Database Schema

```
users
  id, email, username, password_hash, is_admin, created_at

products
  id, url, title, image_url, source_site,
  current_price, currency, last_scraped, scrape_status, created_at

user_products  (watchlist join table)
  id, user_id → users, product_id → products,
  added_at, alert_price
  UNIQUE(user_id, product_id)

price_history  (append-only)
  id, product_id → products, price, scraped_at
  INDEX(product_id, scraped_at)

notifications
  id, user_id → users, product_id → products,
  message, is_read, created_at

scrape_jobs  (audit log)
  id, product_id → products, status, error_message,
  attempted_at, duration_ms
```

**Key design decisions:**
- `user_products` decouples products from users — if two users track the same URL, only one `products` row exists, halving scrape work
- `price_history` is append-only with a composite index on `(product_id, scraped_at)` for fast chart queries
- `scrape_jobs` is a dedicated audit table — operational visibility without polluting `products`

---

## Local Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/price-tracker-platform.git
cd price-tracker-platform
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY and ADMIN_EMAIL at minimum
```

### 3. Start the stack

```bash
docker compose up --build
```

This starts five services: `web`, `db` (PostgreSQL), `redis`, `worker` (Celery), `beat` (Celery Beat).

### 4. Run migrations

```bash
docker compose exec web flask db upgrade
```

### 5. Open the app

Visit [http://localhost:5000](http://localhost:5000)

Register with the email matching `ADMIN_EMAIL` in your `.env` to get admin access automatically.

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session signing key — use a long random string in production |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `ADMIN_EMAIL` | Email that auto-receives admin flag on registration |
| `FLASK_ENV` | `development` or `production` |

---

## Running Tests

```bash
# Run full test suite
docker compose exec web pytest

# With coverage report
docker compose exec web pytest --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database and mocked Celery tasks — no external services required.

---

## CI Pipeline

GitHub Actions runs on every push and pull request to `main`:

1. Install dependencies
2. `flake8` linting
3. `pytest` with coverage

See `.github/workflows/ci.yml`.

---

## Scraping Notes

This project includes a `GenericScraper` that uses BeautifulSoup heuristics to extract prices from product pages. A few important notes:

- **Respect `robots.txt`** — always check a site's robots.txt before scraping in production
- **Rate limiting** — Celery Beat runs scrapes every 60 minutes per product, not continuously
- **User-Agent** — requests use a descriptive User-Agent string
- **Error handling** — failed scrapes are logged to `scrape_jobs` and retried with exponential backoff (max 3 attempts)
- **Legal** — scraping is subject to each site's Terms of Service; this project is for educational purposes

The `ScraperFactory` pattern (Open/Closed Principle) makes it straightforward to add site-specific scrapers without modifying existing code:

```python
# To add an eBay scraper:
# 1. Create app/scraper/ebay.py extending AbstractScraper
# 2. Register it in ScraperFactory.get_scraper()
```

---

## Future Improvements

These are marked as `TODO (stretch)` in the codebase:

- **Real email alerts** — swap the mock email logger for SendGrid or Mailgun
- **Persistent rate limiting** — replace in-memory login throttle with Flask-Limiter + Redis backend
- **Per-site scrapers** — add site-specific subclasses for higher accuracy (eBay, Kogan, JB Hi-Fi)
- **Celery Flower** — task monitoring dashboard
- **REST API + JWT** — expose a JSON API for a future React or mobile frontend
- **OAuth login** — Google / GitHub sign-in via Flask-Dance
- **Price prediction** — trend analysis and "good time to buy" indicator
- **Browser extension** — one-click "track this product" from any product page

---

## Engineering Decisions Worth Noting

| Decision | Rationale |
|---|---|
| `ScraperFactory` pattern | Open/Closed Principle — add new scrapers without touching existing code |
| Deduplicate products by URL | One `products` row per URL regardless of how many users track it — reduces scrape load |
| Separate `scrape_jobs` audit table | Operational visibility without coupling to the `products` table |
| `price_history` append-only | Safe for concurrent writes; full audit trail; no UPDATE contention |
| Services layer separate from routes | Routes handle HTTP; services are testable without a Flask context |
| `create_app` factory pattern | Enables multiple configs (dev/test/prod) without global state |
| Celery Beat for scheduling | Production-grade scheduler — not a cron job or `time.sleep()` loop |

---

## License

MIT
