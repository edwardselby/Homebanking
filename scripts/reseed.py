"""Drop all collections and re-seed the database with sample data.

Usage (with Docker stack running):
    python -m scripts.reseed

Connects using the same settings as the application (HB_MONGODB_URI, etc.).
"""

import asyncio
import logging

from app.config import settings
from app.database import MongoDB
from app.main import ensure_indexes
from app.seed import seed_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

COLLECTIONS = ["users", "accounts", "ledger", "counters"]


async def reset():
    db = MongoDB.get_database()
    for name in COLLECTIONS:
        await db[name].drop()
    logger.info("Dropped collections: %s", ", ".join(COLLECTIONS))

    await ensure_indexes()
    await seed_database()


if __name__ == "__main__":
    asyncio.run(reset())
