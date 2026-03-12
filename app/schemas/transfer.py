from datetime import datetime

from pydantic import BaseModel, Field


class TransferRequest(BaseModel):
    from_account: int = Field(description="Source account number")
    to_account: int = Field(description="Destination account number")
    amount: int = Field(gt=0, description="Transfer amount in cents")


class LedgerEntry(BaseModel):
    """A single immutable record in the append-only ledger.

    :param account_id: The account this entry belongs to.
    :param transfer_id: Groups the debit and credit entries of a transfer.
    :param amount: Positive for credit, negative for debit, in cents.
    :param timestamp: When the entry was created.
    """

    account_id: str
    transfer_id: str
    amount: int
    timestamp: datetime


class TransferResponse(BaseModel):
    """Receipt returned after a successful transfer.

    :param transfer_id: Unique identifier grouping the debit/credit pair.
    :param from_account: Source account number.
    :param to_account: Destination account number.
    :param amount: Transfer amount in cents.
    :param from_balance: Source account balance after transfer.
    :param to_balance: Destination account balance after transfer.
    :param timestamp: When the transfer was executed.
    """

    transfer_id: str
    from_account: int
    to_account: int
    amount: int
    from_balance: int
    to_balance: int
    timestamp: datetime
