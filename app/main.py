import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo.errors import ConnectionFailure

from app.config import settings
from app.database import MongoDB
from app.routes.accounts import router as accounts_router
from app.seed import seed_database
from app.routes.transfers import router as transfers_router
from app.routes.users import router as users_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


async def ensure_indexes():
    """Create required MongoDB indexes and initialise the account-number counter.

    Indexes ensure uniqueness on account numbers and fast lookups on
    ``user_id`` and ``account_id`` foreign keys.  The counter document
    seeds the auto-increment sequence used by
    :func:`~app.routes.accounts.next_account_number`.
    """
    db = MongoDB.get_database()
    await db.accounts.create_index("account_number", unique=True)
    await db.accounts.create_index("user_id")
    await db.ledger.create_index("account_id")
    await db.ledger.create_index("transfer_id")
    await db.counters.update_one(
        {"_id": "account_number"},
        {"$setOnInsert": {"seq": 10000}},
        upsert=True,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan: set up indexes and optionally seed data on startup."""
    await ensure_indexes()
    if settings.seed_on_startup:
        await seed_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(transfers_router)


@app.get("/health")
async def health():
    """Health check that verifies MongoDB connectivity.

    :returns: ``{"status": "ok"}`` if the database is reachable,
        ``{"status": "error", "detail": ...}`` otherwise.
    """
    try:
        await MongoDB.get_client().admin.command("ping")
        return {"status": "ok"}
    except ConnectionFailure as exc:
        return {"status": "error", "detail": str(exc)}
