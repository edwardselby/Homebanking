# Homebanking API

RESTful API for a small bank's homebanking system. Built with FastAPI, MongoDB, and an append-only ledger for financial integrity.

## Quick Start

```bash
docker-compose up
```

API available at [http://localhost:8000](http://localhost:8000). Interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs).

The stack starts with seed data (two users, four accounts with balances) so you can test immediately.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/users` | Create user |
| `GET` | `/api/users` | List users (paginated) |
| `GET` | `/api/users/{id}` | Get single user |
| `PUT` | `/api/users/{id}` | Update user |
| `POST` | `/api/users/{user_id}/accounts` | Create account |
| `GET` | `/api/users/{user_id}/accounts` | List accounts (paginated) |
| `POST` | `/api/transfers` | Transfer between accounts |
| `GET` | `/health` | Health check |

All monetary values are in **integer cents** (e.g. `250000` = $2,500.00).

## Running Tests

Tests require a running MongoDB replica set:

```bash
docker-compose up mongo mongo-init -d
python -m pytest tests/ -v
```

## Tech Stack

- **Python 3.12** / FastAPI / Pydantic v2
- **MongoDB 7** with Motor async driver
- **Append-only ledger** with optimistic concurrency control
- **geopy** (Nominatim) for address geocoding

## Project Structure

```
app/
  main.py              # Entry point, lifespan, indexes
  config.py            # Environment settings (HB_ prefix)
  database.py          # MongoDB connection
  schemas/             # Pydantic request/response models
  routes/              # Endpoint handlers
  services/            # Business logic (transfers, geocoding)
  seed.py              # Sample data for fresh deployments
tests/                 # pytest (transfers, validation, concurrency)
docs/                  # Requirements, decisions, methodology
```

## Documentation

- [Requirements](docs/requirements.md) — acceptance criteria per feature
- [Decisions](docs/DECISIONS.md) — architectural decisions with reasoning
- [Methodology](docs/METHODOLOGY.md) — development approach
- [Overview](docs/OVERVIEW.md) — system description
