"""Test fixtures providing a clean database and HTTP client per test.

Requires a running MongoDB replica set (use ``docker-compose up mongo``).
Tests use a dedicated ``homebanking_test`` database that is dropped after
each test to ensure isolation.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.main import app, ensure_indexes

TEST_DB_NAME = "homebanking_test"


@pytest_asyncio.fixture
async def test_db():
    """Provide a clean test database for each test.

    Creates a fresh Motor client bound to the current event loop, swaps the
    ``db`` reference in all modules, ensures indexes exist, and drops the
    database after the test completes.
    """
    import app.database as database_module
    import app.routes.accounts as accounts_module
    import app.routes.users as users_module
    import app.services.transfer as transfer_module

    test_client = AsyncIOMotorClient(settings.mongodb_uri)
    test_database = test_client[TEST_DB_NAME]

    # Swap db reference in all modules
    database_module.db = test_database
    accounts_module.db = test_database
    users_module.db = test_database
    transfer_module.db = test_database

    # Also swap the client so transactions use the test client
    database_module.client = test_client
    transfer_module.client = test_client

    await ensure_indexes()
    yield test_database
    await test_client.drop_database(TEST_DB_NAME)
    test_client.close()


@pytest_asyncio.fixture
async def http(test_db):
    """Provide an async HTTP client bound to the FastAPI app.

    :param test_db: Ensures the test database is active before requests.
    :returns: An :class:`httpx.AsyncClient` for making test requests.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
