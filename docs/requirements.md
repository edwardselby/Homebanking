# Requirements

Derived from the CluePoints Backend Dev Assessment brief.

---

## R001 — Create user

Create a new user with personal details and address.

`POST /api/users`

**Acceptance criteria:**
- GIVEN a valid payload (name, first name, DOB, address) WHEN the user is created THEN return the user document with a generated ID
- GIVEN a missing required field WHEN the request is submitted THEN return 422 with validation errors
- GIVEN a valid address WHEN the user is created THEN coordinates are computed and stored (see R004)

---

## R002 — Update user

Update an existing user's details.

`PUT /api/users/{user_id}`

**Acceptance criteria:**
- GIVEN a valid user ID and payload WHEN the update is submitted THEN return the updated user document
- GIVEN a non-existent user ID WHEN the update is submitted THEN return 404
- GIVEN an address change WHEN the update is submitted THEN coordinates are recomputed (see R004)
- GIVEN no address change WHEN the update is submitted THEN coordinates are not recomputed

---

## R003 — List users

List all users with pagination.

`GET /api/users?page=1&limit=20`

**Acceptance criteria:**
- GIVEN users exist WHEN the endpoint is called THEN return a paginated list of users
- GIVEN page and limit parameters WHEN the endpoint is called THEN return the correct slice
- GIVEN no parameters WHEN the endpoint is called THEN use sensible defaults (page 1, 20 per page)
- GIVEN a page beyond available data WHEN the endpoint is called THEN return an empty list

---

## R004 — Geocode user address

Automatically compute latitude/longitude from a user's address on create and update.

**Acceptance criteria:**
- GIVEN a user is created with an address WHEN the request completes THEN the user document includes computed coordinates
- GIVEN a user's address is updated WHEN the request completes THEN coordinates reflect the new address
- GIVEN the geocoding service is unavailable WHEN a user is created/updated THEN the request still succeeds with null coordinates
- GIVEN a user is updated without changing the address WHEN the request completes THEN no geocoding call is made

---

## R005 — Create account

Create a new account linked to a user.

`POST /api/users/{user_id}/accounts`

**Acceptance criteria:**
- GIVEN a valid user ID and account type WHEN the account is created THEN return the account with an auto-generated sequential account number
- GIVEN a non-existent user ID WHEN the account is created THEN return 404
- GIVEN a new account WHEN it is created THEN its balance starts at zero (no ledger entries)

---

## R006 — List accounts for a user

List all accounts belonging to a specific user.

`GET /api/users/{user_id}/accounts?page=1&limit=20`

**Acceptance criteria:**
- GIVEN a valid user ID with accounts WHEN the endpoint is called THEN return a paginated list of that user's accounts with current balances
- GIVEN a valid user ID with no accounts WHEN the endpoint is called THEN return an empty list
- GIVEN a non-existent user ID WHEN the endpoint is called THEN return 404
- GIVEN each account WHEN it appears in the list THEN its balance is derived from the sum of its ledger entries

---

## R007 — Transfer money between accounts

Atomically transfer funds from one account to another via the ledger.

`POST /api/transfers`

**Acceptance criteria:**
- GIVEN two valid accounts and sufficient funds WHEN a transfer is submitted THEN a debit entry and credit entry are appended to the ledger within a single transaction
- GIVEN insufficient funds in the source account WHEN a transfer is submitted THEN return 400 and no ledger entries are created
- GIVEN the same account as source and destination WHEN a transfer is submitted THEN return 400
- GIVEN a zero or negative amount WHEN a transfer is submitted THEN return 422 (Pydantic schema validation rejects before business logic)
- GIVEN a non-existent account WHEN a transfer is submitted THEN return 404
- GIVEN a successful transfer WHEN the response is returned THEN include a transfer receipt with both account balances
- GIVEN a failure mid-transaction WHEN the error occurs THEN the transaction is rolled back and no ledger entries persist

---

## R008 — Docker infrastructure

One-command setup for the full stack.

**Acceptance criteria:**
- GIVEN a fresh clone WHEN `docker-compose up` is run THEN the API is available at localhost:8000
- GIVEN the docker-compose stack WHEN it starts THEN MongoDB is configured as a replica set (required for transactions)
- GIVEN the stack is running WHEN `/docs` is visited THEN Swagger UI is available

---

## R009 — Seed data

Pre-loaded data for immediate exploration and review.

**Acceptance criteria:**
- GIVEN a fresh stack WHEN it starts THEN seed users and accounts exist in the database
- GIVEN seed accounts WHEN they are created THEN they have ledger entries representing initial deposits
- GIVEN seed data WHEN the reviewer opens `/docs` THEN they can immediately test endpoints without manual setup
