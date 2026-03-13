# Homebanking API

RESTful API for a small bank's homebanking system. Built with FastAPI, MongoDB, and an append-only ledger for financial integrity.

## Quick Start

```bash
docker-compose up
```

API available at [http://localhost:8000](http://localhost:8000). Interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs).

The stack starts with seed data (two users, four accounts with balances) so you can test immediately.

## Quick Tour

After `docker-compose up`, the seed data includes two users (Alice and Bob) with four accounts. Try these in order:

```bash
# Health check
curl -s localhost:8000/health | python -m json.tool

# List users — see the seed data (Alice and Bob)
curl -s localhost:8000/api/users | python -m json.tool

# Get a single user (replace USER_ID with an id from the list above)
curl -s localhost:8000/api/users/USER_ID | python -m json.tool

# Create a new user — note the coordinates are computed automatically
curl -s -X POST localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Charlie",
    "last_name": "Dumont",
    "date_of_birth": "1992-11-30",
    "address": {
      "street": "Grand Place 1",
      "city": "Brussels",
      "postal_code": "1000",
      "country": "Belgium"
    }
  }' | python -m json.tool

# List accounts for a user (seed accounts start at 10001)
curl -s localhost:8000/api/users/USER_ID/accounts | python -m json.tool

# Transfer £500 from Alice's current (10001) to Bob's current (10003)
curl -s -X POST localhost:8000/api/transfers \
  -H "Content-Type: application/json" \
  -d '{"from_account": 10001, "to_account": 10003, "amount": 50000}' \
  | python -m json.tool

# Try to overdraw — should fail with "Insufficient funds"
curl -s -X POST localhost:8000/api/transfers \
  -H "Content-Type: application/json" \
  -d '{"from_account": 10001, "to_account": 10003, "amount": 99999999}' \
  | python -m json.tool
```

Interactive Swagger docs are also available at [http://localhost:8000/docs](http://localhost:8000/docs).

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

All monetary values are in **integer pence** (e.g. `250000` = £2,500.00).

## Resetting Seed Data

To drop all data and re-seed from scratch (useful after experimenting with transfers):

```bash
docker-compose up mongo mongo-init -d
python -m scripts.reseed
```

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
