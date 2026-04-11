import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING

from bot.config import settings

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_db() -> None:
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.beautybot
    logging.info("Connected to MongoDB")


async def create_indexes() -> None:
    await db.users.create_index("telegram_id", unique=True)
    await db.bookings.create_index("user_id")
    await db.bookings.create_index([("date", ASCENDING), ("time", ASCENDING)])
    await db.blocked_slots.create_index(
        [("date", ASCENDING), ("time", ASCENDING)], unique=True
    )
    logging.info("MongoDB indexes created")


async def close_db() -> None:
    if client:
        client.close()
        logging.info("MongoDB connection closed")
