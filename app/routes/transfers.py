from fastapi import APIRouter

from app.schemas.transfer import TransferRequest, TransferResponse
from app.services.transfer import execute_transfer

router = APIRouter(prefix="/api/transfers", tags=["transfers"])


@router.post("", status_code=201, response_model=TransferResponse)
async def create_transfer(payload: TransferRequest):
    """Transfer money between two accounts.

    Executes an atomic debit/credit via MongoDB transactions. Both ledger
    entries are written within a single transaction — if any step fails
    the entire operation is rolled back.

    :param payload: Source account, destination account, and amount in cents.
    :returns: Transfer receipt with updated balances for both accounts.
    :raises HTTPException: 400 if same account, insufficient funds, or invalid amount.
    :raises HTTPException: 404 if either account does not exist.
    """
    result = await execute_transfer(
        from_account_number=payload.from_account,
        to_account_number=payload.to_account,
        amount=payload.amount,
    )
    return TransferResponse(**result)
