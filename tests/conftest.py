"""Test fixtures providing a clean database and HTTP client per test.

Requires a running MongoDB replica set (use ``docker-compose up mongo``).
Tests use a dedicated ``homebanking_test`` database that is dropped after
each test to ensure isolation.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.database import MongoDB
from app.main import app, ensure_indexes

TEST_DB_NAME = "homebanking_test"


@pytest_asyncio.fixture
async def test_db():
    """Provide a clean test database for each test.

    Creates a fresh Motor client, overrides ``MongoDB.get_database()``
    and ``MongoDB.get_client()`` to return test instances, and drops
    the test database after the test completes.
    """
    test_client = AsyncIOMotorClient(settings.mongodb_uri)
    test_database = test_client[TEST_DB_NAME]

    original_get_db = MongoDB.get_database
    original_get_client = MongoDB.get_client
    MongoDB.get_database = lambda: test_database
    MongoDB.get_client = lambda: test_client

    await ensure_indexes()
    yield test_database

    MongoDB.get_database = original_get_db
    MongoDB.get_client = original_get_client
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
