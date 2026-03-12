from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.database import MongoDB
from app.schemas.account import AccountCreate, AccountResponse

router = APIRouter(prefix="/api/users/{user_id}/accounts", tags=["accounts"])


async def next_account_number() -> int:
    """Atomically increment and return the next account number.

    Uses a MongoDB counter document to guarantee uniqueness across
    concurrent requests without application-level locking.

    :returns: The next sequential account number.
    """
    result = await MongoDB.get_database().counters.find_one_and_update(
        {"_id": "account_number"},
        {"$inc": {"seq": 1}},
        return_document=True,
    )
    return result["seq"]


async def get_balance(account_id: ObjectId) -> int:
    """Derive an account's balance by summing its ledger entries.

    :param account_id: The ``_id`` of the account document.
    :returns: Balance in integer cents, or ``0`` if no entries exist.
    """
    pipeline = [
        {"$match": {"account_id": account_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    result = await MongoDB.get_database().ledger.aggregate(pipeline).to_list(length=1)
    return result[0]["total"] if result else 0


def account_doc_to_response(doc: dict, balance: int = 0) -> AccountResponse:
    """Convert a MongoDB account document to an API response model.

    :param doc: Raw MongoDB document with ``_id`` as :class:`~bson.ObjectId`.
    :param balance: Pre-computed balance in cents from ledger aggregation.
    :returns: Serialisable account response.
    """
    return AccountResponse(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        account_number=doc["account_number"],
        account_type=doc["account_type"],
        balance=balance,
    )


async def validate_user_exists(user_id: str) -> ObjectId:
    """Validate that a user ID is well-formed and exists in the database.

    :param user_id: MongoDB ObjectId as a hex string.
    :returns: The validated :class:`~bson.ObjectId`.
    :raises HTTPException: 404 if the ID is invalid or user not found.
    """
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    oid = ObjectId(user_id)
    if not await MongoDB.get_database().users.find_one({"_id": oid}):
        raise HTTPException(status_code=404, detail="User not found")
    return oid


@router.post("", status_code=201, response_model=AccountResponse)
async def create_account(user_id: str, payload: AccountCreate):
    """Create a new bank account for a user.

    Generates a sequential account number via an atomic MongoDB counter.
    The account starts with a zero balance (no ledger entries).

    :param user_id: MongoDB ObjectId of the owning user.
    :param payload: Account type to create.
    :returns: The created account with generated account number.
    :raises HTTPException: 404 if the user does not exist.
    """
    user_oid = await validate_user_exists(user_id)
    account_number = await next_account_number()
    doc = {
        "user_id": user_oid,
        "account_number": account_number,
        "account_type": payload.account_type,
    }
    result = await MongoDB.get_database().accounts.insert_one(doc)
    doc["_id"] = result.inserted_id
    return account_doc_to_response(doc, balance=0)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    user_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List all accounts for a user with derived balances.

    Each account's balance is computed from the sum of its ledger entries,
    ensuring the response always reflects the true financial state.

    :param user_id: MongoDB ObjectId of the owning user.
    :param page: 1-indexed page number (default ``1``).
    :param limit: Maximum accounts per page, capped at 100 (default ``20``).
    :returns: A list of account responses with current balances.
    :raises HTTPException: 404 if the user does not exist.
    """
    user_oid = await validate_user_exists(user_id)
    skip = (page - 1) * limit
    cursor = MongoDB.get_database().accounts.find({"user_id": user_oid}).skip(skip).limit(limit)
    accounts = await cursor.to_list(length=limit)
    results = []
    for doc in accounts:
        balance = await get_balance(doc["_id"])
        results.append(account_doc_to_response(doc, balance))
    return results
