from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import db
from app.routes.accounts import router as accounts_router
from app.seed import seed_database
from app.routes.transfers import router as transfers_router
from app.routes.users import router as users_router


async def ensure_indexes():
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
async def lifespan(app: FastAPI):
    await ensure_indexes()
    # only seed if env var set, seed also checks for empty database as fallback
    if settings.seed_on_startup:
        await seed_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(transfers_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
