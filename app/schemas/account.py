from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    account_type: str = Field(min_length=1, examples=["current", "savings", "credit_card"])


class AccountResponse(BaseModel):
    """API representation of a bank account.

    :param balance: Derived from the sum of all ledger entries for this
        account, expressed in integer cents.
    """

    id: str
    user_id: str
    account_number: int
    account_type: str
    balance: int = 0
