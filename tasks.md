# Tasks

Ordered implementation plan. Each task is independently verifiable.

---

## Phase 1 — Infrastructure

- [ ] **T01** — Init uv project, install dependencies, export requirements.txt `[D009]`
- [ ] **T02** — Scaffold project structure (app/, schemas/, routes/, services/, tests/)
- [ ] **T03** — Docker-compose with FastAPI + MongoDB replica set `[R008]`
- [ ] **T04** — Database connection module with Motor async client `[R008]`
- [ ] **T05** — App entry point with lifespan events and index creation on startup `[R008, D004]`
- [ ] **T06** — Config module (environment-based settings via Pydantic) `[D001]`

## Phase 2 — Users

- [ ] **T07** — User schemas (create request, update request, document, response) `[D003]`
- [ ] **T08** — POST /api/users — create user `[R001]`
- [ ] **T09** — PUT /api/users/{user_id} — update user `[R002]`
- [ ] **T10** — GET /api/users — list users with pagination `[R003]`
- [ ] **T11** — Geocoding service (address → coordinates via Nominatim) `[R004, D005]`
- [ ] **T12** — Wire geocoding into user create and update routes `[R004]`

## Phase 3 — Accounts

- [ ] **T13** — Account schemas (create request, document, response) `[D003]`
- [ ] **T14** — Account number sequence generator (MongoDB counter document) `[D008]`
- [ ] **T15** — POST /api/users/{user_id}/accounts — create account `[R005]`
- [ ] **T16** — GET /api/users/{user_id}/accounts — list accounts with derived balances `[R006, D007]`

## Phase 4 — Transfers

- [ ] **T17** — Ledger entry schema `[D007, D008]`
- [ ] **T18** — Transfer service — atomic debit/credit within MongoDB transaction `[R007, D007]`
- [ ] **T19** — POST /api/transfers — transfer endpoint with validation `[R007]`

## Phase 5 — Polish

- [ ] **T20** — Seed data script (users, accounts, initial deposit ledger entries) `[R009]`
- [ ] **T21** — Transfer tests (atomicity, insufficient funds, same-account, invalid amounts) `[D006]`
- [ ] **T22** — Validation tests (required fields, types, edge cases) `[D006]`
- [ ] **T23** — Final review — error handling, response consistency, docs check
