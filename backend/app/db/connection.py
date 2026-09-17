"""
db/connection.py — Async MongoDB client with seamless fallback.

Connects to real MongoDB / MongoDB Atlas if available;
falls back to in-memory async Mongo client (mongomock_motor) if local Mongo is not running,
ensuring uninterrupted local development and testing.
"""

from typing import Union
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from mongomock_motor import AsyncMongoMockClient
from app.config import settings

_client: Union[AsyncIOMotorClient, AsyncMongoMockClient, None] = None
_is_mock: bool = False


async def connect_to_mongo() -> None:
    """
    Attempts to connect to MongoDB URI with a fast timeout (2 seconds).
    If unreachable, switches to mongomock_motor seamlessly for local development.
    """
    global _client, _is_mock
    try:
        real_client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=2000
        )
        # Verify server is actually alive
        await real_client.admin.command('ping')
        _client = real_client
        _is_mock = False
        print(f"[DB] Successfully connected to live MongoDB at: {settings.MONGODB_URI}")
    except Exception as e:
        print(f"[DB] Live MongoDB unreachable ({e}). Initializing in-memory database fallback...")
        _client = AsyncMongoMockClient()
        _is_mock = True
        print("[DB] In-memory MongoDB engine active.")


async def close_mongo_connection() -> None:
    """Closes client connection."""
    global _client
    if _client and not _is_mock:
        _client.close()
        print("[DB] MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """Returns the active database instance."""
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized. Was connect_to_mongo() called?")
    return _client[settings.MONGODB_DB_NAME]
