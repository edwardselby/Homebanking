# CluePoints Backend Assessment — Decision Log

This document records architectural decisions, trade-offs, and reasoning throughout development.

---

## D001 — Framework: FastAPI

**Context:** Brief requires Python, bans REST frameworks (DRF, flask-restful). Need JSON-only API.

**Decision:** FastAPI.

**Reasoning:** FastAPI is a web framework, not a REST scaffolding tool — you still write all routes, logic, and validation manually. It gives us type safety via Pydantic and auto-generated OpenAPI docs as a bonus. Flask was the safer choice politically, but FastAPI better reflects how I'd build a real API today.

**Risk:** Reviewer could consider FastAPI too "batteries included." Counter: it doesn't auto-generate CRUD from models (which is what DRF/flask-restful do). All business logic is hand-written.

---

## D002 — Database: MongoDB with Motor

**Context:** Need to store users and accounts. Brief doesn't mandate a specific DB.

**Decision:** MongoDB with the Motor async driver.

**Reasoning:** Document-oriented storage is a natural fit for user profiles with nested address/coordinate data. No ORM mapping overhead. Motor pairs well with FastAPI's async model. Docker-compose makes the dependency trivial for reviewers.

**Trade-off:** MongoDB transactions require a replica set, which adds docker-compose complexity. Accepted — necessary for reliable money transfers.

---

## D003 — No separate models layer

**Context:** Typical REST apps separate ORM models from API schemas. With MongoDB there's no ORM.

**Decision:** Pydantic schemas serve dual purpose — API validation and document shape definition. No `models/` directory.

**Reasoning:** Adding a separate models layer would be artificial abstraction with no ORM to justify it. Keeps the codebase lean. If this grew to need ODM (e.g. Beanie), we'd revisit.

---

## D004 — Migrations: startup index script over pymongo-migrate

**Context:** MongoDB is schemaless, so traditional migrations are lightweight. Mainly needed for indexes.

**Decision:** App startup function that ensures indexes exist (unique on account number, index on user_id in accounts collection, etc.).

**Reasoning:** pymongo-migrate adds a dependency for something we can handle in ~20 lines. For an MVP, a startup script is more transparent and easier for reviewers to follow. Migrations would make sense at scale for data backfills or document restructuring.

---

## D005 — Geocoding: geopy + Nominatim

**Context:** Brief requires address coordinates to be computed by the application on user create/update.

**Decision:** Use geopy with the Nominatim geocoder (OpenStreetMap).

**Reasoning:** Free, no API key, well-documented. Adequate for an MVP. Triggers only when address is provided (create) or changed (update) — avoids unnecessary API calls.

**Limitation:** Nominatim has a 1 request/second rate limit. Fine for an assessment, would need a paid provider at scale.

---

## D006 — Testing scope: transfers + validation only

**Context:** Brief emphasises best practices. Full test suite would be ideal but time is limited.

**Decision:** pytest with focused tests on money transfer reliability and input validation.

**Reasoning:** These are the two areas most likely to have subtle bugs and the areas the assessment is most clearly testing. Transfer tests cover atomicity, insufficient funds, same-account rejection, invalid amounts. Validation tests cover required fields, data types, edge cases.

---

## D007 — Ledger pattern over direct balance mutation

**Context:** Money transfers can be implemented two ways: mutate a balance field directly, or append immutable ledger entries and derive the balance. The hiring manager explicitly asked for production-quality design.

**Decision:** Append-only ledger. Every transfer creates two entries (debit and credit). Account balance is always derived by summing ledger entries — no mutable balance field.

**Reasoning:** This is how production financial systems work. A mutable balance can drift out of sync, has no audit trail, and loses history. The ledger gives us traceability, auditability, and a single source of truth. Choosing direct mutation for an assessment that asks for production thinking would undermine the brief.

**Trade-off:** Balance lookups require aggregation across ledger entries, which is slower than reading a single field. At scale you'd add materialised balance views or periodic snapshots. For this assessment, the data volume doesn't justify that optimisation — we accept the aggregation cost to keep the implementation honest and simple.

---

## D008 — Money stored as integer cents

**Context:** Financial amounts need precise representation. Floats introduce rounding errors (e.g. `0.1 + 0.2 ≠ 0.3`).

**Decision:** Store all monetary values as integers representing cents/pence. The API accepts and returns cents. Presentation formatting is a frontend concern.

**Reasoning:** Integer arithmetic is exact, avoids IEEE 754 surprises, and is the standard approach in payment systems (Stripe, banking cores). Decimal was considered but adds serialisation complexity with MongoDB for no real benefit at this scale.

---

## D009 — Dependency management: uv with requirements.txt export

**Context:** Need reproducible dependency management. Options: pip + requirements.txt, Poetry, uv.

**Decision:** Use uv for development (lockfile, fast resolution) and export a `requirements.txt` for compatibility. Dockerfile uses `pip install -r requirements.txt` so reviewers don't need uv installed.

**Reasoning:** uv is the modern standard for Python packaging — fast, handles virtualenvs and lockfiles natively. Exporting requirements.txt keeps the Docker build simple and universally compatible.

---

## D010 — Docstring format: reStructuredText

**Context:** Need a consistent docstring convention across the codebase.

**Decision:** Use reStructuredText (rST) field lists (`:param:`, `:returns:`, `:raises:`) for all public functions and methods.

**Reasoning:** rST is the native format for Sphinx and the most widely adopted convention in the Python ecosystem. It keeps docstrings machine-parseable for documentation generation while remaining readable in source. Google and NumPy styles were considered but rST is more appropriate for a backend API codebase of this size.

---

## Resolved Questions

- **Account number generation** — Auto-generated sequential integer (e.g. `10001`, `10002`). MongoDB ObjectId used internally; the account number is the user-facing identifier. Sequence managed via a MongoDB counter document.
- **Account listing by user** — Nested route `GET /api/users/{user_id}/accounts` rather than query parameter filtering. Expresses the ownership relationship in the URL and gives a proper 404 when the user doesn't exist.
