"""Input validation tests covering required fields, types, and edge cases.

Maps to requirements R001, R002, R005, and R007.
"""

import pytest


VALID_USER = {
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1995-06-15",
    "address": {
        "street": "123 Main St",
        "city": "Brussels",
        "postal_code": "1000",
        "country": "Belgium",
    },
}


class TestUserValidation:
    """Validation tests for user creation and update endpoints."""

    @pytest.mark.asyncio
    async def test_create_user_missing_first_name(self, http):
        """GIVEN a missing first_name WHEN creating a user THEN return 422."""
        payload = {**VALID_USER}
        del payload["first_name"]
        resp = await http.post("/api/users", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_empty_first_name(self, http):
        """GIVEN an empty first_name WHEN creating a user THEN return 422."""
        payload = {**VALID_USER, "first_name": ""}
        resp = await http.post("/api/users", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_missing_address(self, http):
        """GIVEN a missing address WHEN creating a user THEN return 422."""
        payload = {**VALID_USER}
        del payload["address"]
        resp = await http.post("/api/users", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_invalid_date_format(self, http):
        """GIVEN a malformed date WHEN creating a user THEN return 422."""
        payload = {**VALID_USER, "date_of_birth": "not-a-date"}
        resp = await http.post("/api/users", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_partial_address(self, http):
        """GIVEN an address missing required fields WHEN creating a user
        THEN return 422."""
        payload = {**VALID_USER, "address": {"street": "123 Main St"}}
        resp = await http.post("/api/users", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_success(self, http):
        """GIVEN a valid payload WHEN creating a user THEN return 201."""
        resp = await http.post("/api/users", json=VALID_USER)
        assert resp.status_code == 201
        data = resp.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, http):
        """GIVEN a nonexistent user ID WHEN updating THEN return 404."""
        resp = await http.put("/api/users/000000000000000000000000", json={
            "first_name": "Updated",
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_invalid_object_id(self, http):
        """GIVEN an invalid ObjectId WHEN updating THEN return 404."""
        resp = await http.put("/api/users/not-an-id", json={
            "first_name": "Updated",
        })
        assert resp.status_code == 404


class TestAccountValidation:
    """Validation tests for account creation."""

    @pytest.mark.asyncio
    async def test_create_account_missing_type(self, http):
        """GIVEN a missing account_type WHEN creating an account THEN return 422."""
        user_resp = await http.post("/api/users", json=VALID_USER)
        user_id = user_resp.json()["id"]
        resp = await http.post(f"/api/users/{user_id}/accounts", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_account_empty_type(self, http):
        """GIVEN an empty account_type WHEN creating an account THEN return 422."""
        user_resp = await http.post("/api/users", json=VALID_USER)
        user_id = user_resp.json()["id"]
        resp = await http.post(f"/api/users/{user_id}/accounts", json={
            "account_type": "",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_account_nonexistent_user(self, http):
        """GIVEN a nonexistent user WHEN creating an account THEN return 404."""
        resp = await http.post(
            "/api/users/000000000000000000000000/accounts",
            json={"account_type": "current"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_account_success(self, http):
        """GIVEN a valid user and type WHEN creating an account THEN return 201
        with a sequential account number and zero balance."""
        user_resp = await http.post("/api/users", json=VALID_USER)
        user_id = user_resp.json()["id"]
        resp = await http.post(f"/api/users/{user_id}/accounts", json={
            "account_type": "current",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["account_type"] == "current"
        assert data["balance"] == 0
        assert isinstance(data["account_number"], int)


class TestTransferValidation:
    """Validation tests for transfer request payloads."""

    @pytest.mark.asyncio
    async def test_transfer_missing_amount(self, http):
        """GIVEN a missing amount WHEN submitting a transfer THEN return 422."""
        resp = await http.post("/api/transfers", json={
            "from_account": 10001,
            "to_account": 10002,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_transfer_string_amount(self, http):
        """GIVEN a string amount WHEN submitting a transfer THEN return 422."""
        resp = await http.post("/api/transfers", json={
            "from_account": 10001,
            "to_account": 10002,
            "amount": "fifty",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_transfer_missing_accounts(self, http):
        """GIVEN missing account fields WHEN submitting a transfer THEN return 422."""
        resp = await http.post("/api/transfers", json={"amount": 1000})
        assert resp.status_code == 422
