from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.constants import TIME_SLOTS
from bot.database.models import BlockedSlot, Booking, User


async def get_free_slots(session: AsyncSession, date_str: str) -> list[str]:
    """Возвращает доступные временные слоты для указанной даты."""
    # Занятые записи (pending или confirmed)
    result = await session.execute(
        select(Booking.time).where(
            Booking.date == date_str,
            Booking.status.in_(["pending", "confirmed"]),
        )
    )
    booked_times = {row[0] for row in result.fetchall()}

    # Заблокированные слоты
    blocked_result = await session.execute(
        select(BlockedSlot.time).where(BlockedSlot.date == date_str)
    )
    blocked_times = {row[0] for row in blocked_result.fetchall()}

    occupied = booked_times | blocked_times
    return [slot for slot in TIME_SLOTS if slot not in occupied]


async def has_active_booking(session: AsyncSession, user_db_id: int) -> bool:
    """Проверяет, есть ли у пользователя активная запись (pending или confirmed)."""
    result = await session.execute(
        select(Booking.id).where(
            Booking.user_id == user_db_id,
            Booking.status.in_(["pending", "confirmed"]),
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def get_user_active_bookings(session: AsyncSession, user_db_id: int) -> list[Booking]:
    """Возвращает все активные записи пользователя."""
    result = await session.execute(
        select(Booking).where(
            Booking.user_id == user_db_id,
            Booking.status.in_(["pending", "confirmed"]),
        ).order_by(Booking.date, Booking.time)
    )
    return list(result.scalars().all())
