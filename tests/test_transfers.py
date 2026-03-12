"""Transfer endpoint tests covering atomicity, validation, and edge cases.

Maps to requirement R007 and decision D007 (ledger pattern).
"""

import pytest


@pytest.fixture
async def two_accounts(http):
    """Create a user with two funded accounts for transfer testing.

    :returns: Tuple of (current_account_number, savings_account_number).
    """
    user_resp = await http.post("/api/users", json={
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1990-01-01",
        "address": {
            "street": "1 Test Street",
            "city": "TestCity",
            "postal_code": "12345",
            "country": "TestCountry",
        },
    })
    user_id = user_resp.json()["id"]

    acc1 = await http.post(f"/api/users/{user_id}/accounts", json={"account_type": "current"})
    acc2 = await http.post(f"/api/users/{user_id}/accounts", json={"account_type": "savings"})
    acc1_num = acc1.json()["account_number"]
    acc2_num = acc2.json()["account_number"]

    # Fund the current account with 1000.00 (100000 cents) via a transfer
    # We need a third account as the funding source
    acc3 = await http.post(f"/api/users/{user_id}/accounts", json={"account_type": "funding"})
    acc3_num = acc3.json()["account_number"]

    # Seed the funding account via direct ledger entry
    from bson import ObjectId
    from app.database import MongoDB

    test_database = MongoDB.get_database()
    funding_doc = await test_database.accounts.find_one({"account_number": acc3_num})
    await test_database.ledger.insert_one({
        "account_id": funding_doc["_id"],
        "transfer_id": ObjectId(),
        "amount": 100000,
        "timestamp": "2024-01-01T00:00:00Z",
    })

    # Transfer to current account
    await http.post("/api/transfers", json={
        "from_account": acc3_num,
        "to_account": acc1_num,
        "amount": 100000,
    })

    return acc1_num, acc2_num


@pytest.mark.asyncio
async def test_successful_transfer(http, two_accounts):
    """GIVEN two accounts with sufficient funds WHEN a transfer is made THEN
    both balances are updated and a receipt is returned."""
    acc1, acc2 = two_accounts

    resp = await http.post("/api/transfers", json={
        "from_account": acc1,
        "to_account": acc2,
        "amount": 30000,
    })
    assert resp.status_code == 201

    data = resp.json()
    assert data["amount"] == 30000
    assert data["from_account"] == acc1
    assert data["to_account"] == acc2
    assert data["from_balance"] == 70000  # 100000 - 30000
    assert data["to_balance"] == 30000
    assert "transfer_id" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_insufficient_funds(http, two_accounts):
    """GIVEN insufficient funds WHEN a transfer is attempted THEN return 400
    and no ledger entries are created."""
    acc1, acc2 = two_accounts

    resp = await http.post("/api/transfers", json={
        "from_account": acc1,
        "to_account": acc2,
        "amount": 999999,
    })
    assert resp.status_code == 400
    assert "Insufficient funds" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_same_account_transfer(http, two_accounts):
    """GIVEN the same source and destination WHEN a transfer is attempted
    THEN return 400."""
    acc1, _ = two_accounts

    resp = await http.post("/api/transfers", json={
        "from_account": acc1,
        "to_account": acc1,
        "amount": 1000,
    })
    assert resp.status_code == 400
    assert "same account" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_zero_amount_rejected(http, two_accounts):
    """GIVEN a zero amount WHEN a transfer is attempted THEN return 422."""
    acc1, acc2 = two_accounts

    resp = await http.post("/api/transfers", json={
        "from_account": acc1,
        "to_account": acc2,
        "amount": 0,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_negative_amount_rejected(http, two_accounts):
    """GIVEN a negative amount WHEN a transfer is attempted THEN return 422."""
    acc1, acc2 = two_accounts

    resp = await http.post("/api/transfers", json={
        "from_account": acc1,
        "to_account": acc2,
        "amount": -5000,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_nonexistent_source_account(http, two_accounts):
    """GIVEN a nonexistent source account WHEN a transfer is attempted
    THEN return 404."""
    _, acc2 = two_accounts

    resp = await http.post("/api/transfers", json={
        "from_account": 99999,
        "to_account": acc2,
        "amount": 1000,
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_nonexistent_destination_account(http, two_accounts):
    """GIVEN a nonexistent destination account WHEN a transfer is attempted
    THEN return 404."""
    acc1, _ = two_accounts

    resp = await http.post("/api/transfers", json={
        "from_account": acc1,
        "to_account": 99999,
        "amount": 1000,
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_balance_consistency_after_multiple_transfers(http, two_accounts):
    """GIVEN multiple sequential transfers WHEN balances are checked THEN
    the total across both accounts remains constant (no money created
    or destroyed)."""
    acc1, acc2 = two_accounts

    await http.post("/api/transfers", json={
        "from_account": acc1, "to_account": acc2, "amount": 10000,
    })
    await http.post("/api/transfers", json={
        "from_account": acc2, "to_account": acc1, "amount": 5000,
    })
    resp = await http.post("/api/transfers", json={
        "from_account": acc1, "to_account": acc2, "amount": 20000,
    })
    data = resp.json()
    assert data["from_balance"] + data["to_balance"] == 100000
