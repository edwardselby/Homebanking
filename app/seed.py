"""Seed the database with sample users, accounts, and initial deposits.

Run via the application lifespan on startup. Skips seeding if data
already exists to allow safe restarts.
"""

import logging
from datetime import date, datetime, timezone

from bson import ObjectId

from app.database import MongoDB

logger = logging.getLogger(__name__)

SEED_USERS = [
    {
        "first_name": "Alice",
        "last_name": "Martin",
        "date_of_birth": date(1990, 3, 15).isoformat(),
        "address": {
            "street": "10 Downing Street",
            "city": "London",
            "state": None,
            "postal_code": "SW1A 2AA",
            "country": "United Kingdom",
        },
        "coordinates": {"latitude": 51.5034, "longitude": -0.1276},
    },
    {
        "first_name": "Bob",
        "last_name": "Dupont",
        "date_of_birth": date(1985, 7, 22).isoformat(),
        "address": {
            "street": "Rue de la Loi 16",
            "city": "Brussels",
            "state": None,
            "postal_code": "1000",
            "country": "Belgium",
        },
        "coordinates": {"latitude": 50.8467, "longitude": 4.3525},
    },
]

SEED_ACCOUNTS = [
    {"user_index": 0, "account_type": "current"},
    {"user_index": 0, "account_type": "savings"},
    {"user_index": 1, "account_type": "current"},
    {"user_index": 1, "account_type": "savings"},
]

INITIAL_DEPOSITS = [
    {"account_index": 0, "amount": 250000},  # Alice current: 2500.00
    {"account_index": 1, "amount": 100000},  # Alice savings: 1000.00
    {"account_index": 2, "amount": 175000},  # Bob current: 1750.00
    {"account_index": 3, "amount": 50000},   # Bob savings: 500.00
]


async def seed_database():
    """Populate the database with sample data if empty.

    Creates two users (Alice and Bob) each with a current and savings
    account. Initial balances are established via ledger entries to
    stay consistent with the append-only ledger pattern.

    Skips entirely if any users already exist in the database.
    """
    if await MongoDB.get_database().users.count_documents({}) > 0:
        logger.info("Database already seeded, skipping")
        return

    logger.info("Seeding database with sample data...")

    # Insert users
    user_ids = []
    for user_data in SEED_USERS:
        result = await MongoDB.get_database().users.insert_one(user_data)
        user_ids.append(result.inserted_id)

    # Insert accounts with sequential numbers
    account_ids = []
    for account_data in SEED_ACCOUNTS:
        counter = await MongoDB.get_database().counters.find_one_and_update(
            {"_id": "account_number"},
            {"$inc": {"seq": 1}},
            return_document=True,
        )
        doc = {
            "user_id": user_ids[account_data["user_index"]],
            "account_number": counter["seq"],
            "account_type": account_data["account_type"],
            "version": 0,
        }
        result = await MongoDB.get_database().accounts.insert_one(doc)
        account_ids.append(result.inserted_id)

    # Insert initial deposit ledger entries — each deposit gets its own
    # transfer_id since they are independent funding events.
    now = datetime.now(timezone.utc)
    ledger_entries = [
        {
            "account_id": account_ids[dep["account_index"]],
            "transfer_id": ObjectId(),
            "amount": dep["amount"],
            "timestamp": now,
        }
        for dep in INITIAL_DEPOSITS
    ]
    await MongoDB.get_database().ledger.insert_many(ledger_entries)

    logger.info("Seeded %d users, %d accounts, %d ledger entries",
                len(SEED_USERS), len(SEED_ACCOUNTS), len(ledger_entries))
