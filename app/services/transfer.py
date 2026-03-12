from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException

from app.database import client, db


async def get_balance_in_session(account_id: ObjectId, session) -> int:
    """Derive an account's balance within a transaction session.

    :param account_id: The ``_id`` of the account document.
    :param session: Active MongoDB client session for transactional reads.
    :returns: Balance in integer cents, or ``0`` if no entries exist.
    """
    pipeline = [
        {"$match": {"account_id": account_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    result = await db.ledger.aggregate(pipeline, session=session).to_list(length=1)
    return result[0]["total"] if result else 0


async def execute_transfer(
    from_account_number: int,
    to_account_number: int,
    amount: int,
) -> dict:
    """Atomically transfer funds between two accounts via the ledger.

    Runs inside a MongoDB transaction to guarantee that either both the
    debit and credit entries are persisted, or neither is. Validates
    account existence, distinctness, and sufficient funds before writing.

    :param from_account_number: Source account number (user-facing).
    :param to_account_number: Destination account number (user-facing).
    :param amount: Transfer amount in positive integer cents.
    :returns: A dict containing transfer receipt data.
    :raises HTTPException: 400 if accounts are identical or funds insufficient.
    :raises HTTPException: 404 if either account does not exist.
    """
    if from_account_number == to_account_number:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    async with await client.start_session() as session:
        async with session.start_transaction():
            from_doc = await db.accounts.find_one(
                {"account_number": from_account_number}, session=session
            )
            if not from_doc:
                raise HTTPException(status_code=404, detail="Source account not found")

            to_doc = await db.accounts.find_one(
                {"account_number": to_account_number}, session=session
            )
            if not to_doc:
                raise HTTPException(status_code=404, detail="Destination account not found")

            from_balance = await get_balance_in_session(from_doc["_id"], session)
            if from_balance < amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")

            transfer_id = ObjectId()
            now = datetime.now(timezone.utc)

            await db.ledger.insert_many(
                [
                    {
                        "account_id": from_doc["_id"],
                        "transfer_id": transfer_id,
                        "amount": -amount,
                        "timestamp": now,
                    },
                    {
                        "account_id": to_doc["_id"],
                        "transfer_id": transfer_id,
                        "amount": amount,
                        "timestamp": now,
                    },
                ],
                session=session,
            )

            new_from_balance = await get_balance_in_session(from_doc["_id"], session)
            new_to_balance = await get_balance_in_session(to_doc["_id"], session)

    return {
        "transfer_id": str(transfer_id),
        "from_account": from_account_number,
        "to_account": to_account_number,
        "amount": amount,
        "from_balance": new_from_balance,
        "to_balance": new_to_balance,
        "timestamp": now,
    }
