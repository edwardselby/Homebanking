from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import db


async def ensure_indexes():
    await db.users.create_index("email", unique=True, sparse=True)
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
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
