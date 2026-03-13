# Homebanking API — Overview

A RESTful API for a small bank's homebanking system, enabling cross-device access to user and account management.

## Tech Stack

- **Runtime:** Python 3.12+
- **Framework:** FastAPI
- **Database:** MongoDB (Motor async driver)
- **Geocoding:** geopy (Nominatim/OpenStreetMap)
- **Validation:** Pydantic v2
- **Testing:** pytest
- **Infrastructure:** Docker + docker-compose

## Project Structure

```
homebanking/
├── app/
│   ├── __init__.py
│   ├── main.py              # App entry point, lifespan events, index setup
│   ├── config.py            # Environment-based settings
│   ├── database.py          # Motor client and DB connection
│   ├── schemas/
│   │   ├── user.py          # User request/response/document schemas
│   │   ├── account.py       # Account schemas
│   │   ├── transfer.py      # Transfer request/response schemas
│   ├── routes/
│   │   ├── users.py         # User endpoints
│   │   ├── accounts.py      # Account endpoints
│   │   ├── transfers.py     # Transfer endpoint
│   ├── services/
│   │   ├── geocoding.py     # Address → coordinates via Nominatim
│   │   ├── transfer.py      # Atomic money transfer logic
├── tests/
│   ├── conftest.py
│   ├── test_transfers.py
│   ├── test_validation.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users` | List users (paginated) |
| POST | `/api/users` | Create user |
| PUT | `/api/users/{id}` | Update user |
| GET | `/api/accounts` | List accounts (paginated) |
| POST | `/api/accounts` | Create account |
| POST | `/api/transfers` | Transfer between accounts |

Auto-generated documentation at `/docs` (Swagger UI) and `/redoc`.

## Core Features

**Money Transfers** — Atomic debit/credit using MongoDB transactions. Validates sufficient funds, rejects same-account transfers and invalid amounts. Rolls back on any failure.

**Geocoding** — Coordinates are automatically computed from a user's address on create and update (only when address changes). Uses OpenStreetMap's Nominatim service.

**Pagination** — List endpoints accept `?page=1&per_page=20` query parameters.

## Running

```bash
docker-compose up
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.
