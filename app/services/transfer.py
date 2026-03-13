import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from pymongo import ReadPreference
from pymongo.errors import OperationFailure
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

from app.database import MongoDB

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


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
    result = (
        await MongoDB.get_database()
        .ledger.aggregate(pipeline, session=session)
        .to_list(length=1)
    )
    return result[0]["total"] if result else 0


async def execute_transfer(
    from_account_number: int,
    to_account_number: int,
    amount: int,
) -> dict:
    """Atomically transfer funds between two accounts via the ledger.

    Uses optimistic concurrency control: each account document carries a
    ``version`` counter that is incremented inside the transaction. If a
    concurrent transfer modifies the same account, the version check fails
    (``matched_count == 0``) and the transaction is retried. This avoids
    the need for pessimistic locks while guaranteeing that the balance
    check cannot be bypassed by concurrent requests.

    The ledger remains the sole authoritative source for balances — no
    denormalised balance cache is stored on the account document.

    :param from_account_number: Source account number (user-facing).
    :param to_account_number: Destination account number (user-facing).
    :param amount: Transfer amount in positive integer cents.
    :returns: A dict containing transfer receipt data.
    :raises HTTPException: 400 if accounts are identical or funds insufficient.
    :raises HTTPException: 404 if either account does not exist.
    :raises HTTPException: 409 if the transfer could not be completed due to contention.
    """
    if from_account_number == to_account_number:
        raise HTTPException(
            status_code=400, detail="Cannot transfer to the same account"
        )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await _try_transfer(from_account_number, to_account_number, amount)
        except _WriteConflict:
            logger.warning(
                "Transfer write conflict (attempt %d/%d): %s -> %s, %d cents",
                attempt,
                MAX_RETRIES,
                from_account_number,
                to_account_number,
                amount,
            )
            if attempt == MAX_RETRIES:
                raise HTTPException(
                    status_code=409,
                    detail="Transfer could not be completed due to contention,"
                    " please retry",
                )


class _WriteConflict(Exception):
    """Raised when an optimistic version check fails inside a transaction."""


async def _try_transfer(
    from_account_number: int,
    to_account_number: int,
    amount: int,
) -> dict:
    """Attempt a single transfer inside a MongoDB transaction.

    :raises _WriteConflict: If a concurrent transaction modified the same
        account (version mismatch or transient transaction error).
    :raises HTTPException: For business rule violations (404, 400).
    """
    db = MongoDB.get_database()

    async with await MongoDB.get_client().start_session() as session:
        try:
            async with session.start_transaction(
                read_concern=ReadConcern("snapshot"),
                write_concern=WriteConcern(w="majority"),
                read_preference=ReadPreference.PRIMARY,
            ):
                from_doc = await db.accounts.find_one(
                    {"account_number": from_account_number}, session=session
                )
                if not from_doc:
                    raise HTTPException(
                        status_code=404, detail="Source account not found"
                    )

                to_doc = await db.accounts.find_one(
                    {"account_number": to_account_number}, session=session
                )
                if not to_doc:
                    raise HTTPException(
                        status_code=404, detail="Destination account not found"
                    )

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

                # Optimistic concurrency: bump the version on both accounts.
                # If another transaction already bumped the version since our
                # snapshot read, matched_count will be 0 and we retry.
                from_version = from_doc.get("version", 0)
                result = await db.accounts.update_one(
                    {"_id": from_doc["_id"], "version": from_version},
                    {"$set": {"version": from_version + 1}},
                    session=session,
                )
                if result.matched_count == 0:
                    raise _WriteConflict()

                to_version = to_doc.get("version", 0)
                result = await db.accounts.update_one(
                    {"_id": to_doc["_id"], "version": to_version},
                    {"$set": {"version": to_version + 1}},
                    session=session,
                )
                if result.matched_count == 0:
                    raise _WriteConflict()

                new_from_balance = from_balance - amount
                new_to_balance = await get_balance_in_session(to_doc["_id"], session)

        except OperationFailure as exc:
            if exc.has_error_label("TransientTransactionError"):
                raise _WriteConflict() from exc
            raise

    return {
        "transfer_id": str(transfer_id),
        "from_account": from_account_number,
        "to_account": to_account_number,
        "amount": amount,
        "from_balance": new_from_balance,
        "to_balance": new_to_balance,
        "timestamp": now,
    }
