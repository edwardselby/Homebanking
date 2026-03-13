from typing import Literal

from pydantic import BaseModel, Field

AccountType = Literal["current", "savings"]


class AccountCreate(BaseModel):
    account_type: AccountType


class AccountResponse(BaseModel):
    """API representation of a bank account.

    :param balance: Derived from the sum of all ledger entries for this
        account, expressed in integer cents.
    """

    id: str
    user_id: str
    account_number: int
    account_type: AccountType
    balance: int = 0
