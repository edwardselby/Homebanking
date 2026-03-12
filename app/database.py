from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


class MongoDB:
    """Singleton-style database accessor.

    The client and database are accessed via class methods so that test
    fixtures can swap the underlying reference without stale module-level
    bindings.
    """

    _client: AsyncIOMotorClient | None = None
    _db = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls._client is None:
            cls._client = AsyncIOMotorClient(settings.mongodb_uri)
        return cls._client

    @classmethod
    def get_database(cls):
        if cls._db is None:
            cls._db = cls.get_client()[settings.database_name]
        return cls._db
