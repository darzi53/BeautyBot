from motor.motor_asyncio import AsyncIOMotorDatabase

from bot.constants import TIME_SLOTS


async def get_free_slots(db: AsyncIOMotorDatabase, date_str: str) -> list[str]:
    """Возвращает доступные временные слоты для указанной даты."""
    booked = await db.bookings.distinct(
        "time",
        {"date": date_str, "status": {"$in": ["pending", "confirmed"]}},
    )
    blocked = await db.blocked_slots.distinct("time", {"date": date_str})
    occupied = set(booked) | set(blocked)
    return [slot for slot in TIME_SLOTS if slot not in occupied]


async def has_active_booking(db: AsyncIOMotorDatabase, user_id_str: str) -> bool:
    """Проверяет, есть ли у пользователя активная запись (pending или confirmed)."""
    count = await db.bookings.count_documents({
        "user_id": user_id_str,
        "status": {"$in": ["pending", "confirmed"]},
    })
    return count > 0


async def get_user_active_bookings(db: AsyncIOMotorDatabase, user_id_str: str) -> list[dict]:
    """Возвращает все активные записи пользователя."""
    cursor = db.bookings.find(
        {"user_id": user_id_str, "status": {"$in": ["pending", "confirmed"]}},
    ).sort([("date", 1), ("time", 1)])
    return await cursor.to_list(length=None)
