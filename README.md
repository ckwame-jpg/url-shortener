# URL Shortener

[![CI](https://github.com/ckwame-jpg/url-shortener/actions/workflows/ci.yml/badge.svg)](https://github.com/ckwame-jpg/url-shortener/actions/workflows/ci.yml)

A URL shortener with async click analytics. Shorten URLs, track clicks, and view analytics - all behind JWT auth. Redirects are fast because click processing happens in the background via Celery workers.

## Tech Stack

- **FastAPI** - Python web framework
- **PostgreSQL** - persistent storage
- **Redis** - caching + Celery message broker
- **Celery** - background worker for click analytics
- **SQLAlchemy** - ORM
- **Docker Compose** - full stack orchestration
- **pytest** - test suite

## Quick Start

```bash
docker compose up
```

This spins up four services:
- **api** - FastAPI on port 8000
- **worker** - Celery worker processing click events
- **postgres** - PostgreSQL database
- **redis** - cache and message broker

API docs at: http://localhost:8000/docs

## How It Works

1. Create an account and shorten a URL
2. When someone visits the short link, they get redirected immediately
3. A Celery task fires in the background to log the click (device type, referrer, IP)
4. View analytics for your URLs - total clicks, top referrers, device breakdown

The redirect stays fast because analytics processing is async.

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | No | Create account |
| POST | `/login` | No | Get JWT token |

### URLs

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/shorten` | Yes | Create short URL |
| GET | `/urls` | Yes | List your URLs |
| DELETE | `/urls/{code}` | Yes | Delete a URL |
| GET | `/{code}` | No | Redirect to original |

### Analytics

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/urls/{code}/stats` | Yes | Click analytics |

### Example

```bash
# Register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass"}'

# Login
curl -X POST http://localhost:8000/login \
  -d "username=user@example.com&password=securepass"

# Shorten a URL
curl -X POST http://localhost:8000/shorten \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com"}'

# Check analytics
curl http://localhost:8000/urls/abc1234/stats \
  -H "Authorization: Bearer <token>"
```

## Running Tests

```bash
pip install -r requirements.txt
pytest -v
```

```text
tests/test_auth.py::test_register                PASSED
tests/test_auth.py::test_register_duplicate       PASSED
tests/test_auth.py::test_login_success            PASSED
tests/test_auth.py::test_login_wrong_password     PASSED
tests/test_auth.py::test_login_nonexistent_user   PASSED
tests/test_urls.py::test_shorten_url              PASSED
tests/test_urls.py::test_shorten_requires_auth    PASSED
tests/test_urls.py::test_list_urls                PASSED
tests/test_urls.py::test_delete_url               PASSED
tests/test_urls.py::test_delete_not_found         PASSED
tests/test_urls.py::test_redirect                 PASSED
tests/test_urls.py::test_redirect_not_found       PASSED
tests/test_analytics.py::test_stats_empty         PASSED
tests/test_analytics.py::test_stats_with_clicks   PASSED
tests/test_analytics.py::test_stats_not_found     PASSED
tests/test_analytics.py::test_stats_requires_auth PASSED
```

## Project Structure

```text
url-shortener/
├── app/
│   ├── main.py           # FastAPI app setup
│   ├── database.py       # SQLAlchemy config
│   ├── models.py         # User, URL, Click models
│   ├── schemas.py        # Pydantic schemas
│   ├── auth.py           # JWT authentication
│   ├── redis_client.py   # Redis connection
│   ├── celery_app.py     # Celery configuration
│   ├── tasks.py          # Background tasks
│   └── routes/
│       ├── users.py      # Register/login
│       ├── urls.py       # URL shortening + redirect
│       └── analytics.py  # Click analytics
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Built By

Christopher Prempeh
