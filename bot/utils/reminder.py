from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

TZ = ZoneInfo("Asia/Tashkent")

scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")


async def schedule_reminder(
    bot,
    booking_id: int,
    date_str: str,
    time_str: str,
    user_telegram_id: int,
    service_name: str,
    date_long: str,
) -> None:
    """Планирует отправку напоминания за 24 часа до записи."""
    hour, minute = map(int, time_str.split(":"))
    year, month, day = map(int, date_str.split("-"))
    booking_dt = datetime(year, month, day, hour, minute, tzinfo=TZ)
    remind_at = booking_dt - timedelta(hours=24)

    if remind_at > datetime.now(TZ):
        job_id = f"reminder_{booking_id}"
        # Убираем старый джоб если есть (повторная запись)
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        scheduler.add_job(
            send_reminder,
            "date",
            run_date=remind_at,
            args=[bot, user_telegram_id, service_name, date_long, time_str],
            id=job_id,
        )


async def send_reminder(
    bot,
    user_telegram_id: int,
    service_name: str,
    date_long: str,
    time_str: str,
) -> None:
    """Отправляет напоминание о записи пользователю."""
    try:
        await bot.send_message(
            user_telegram_id,
            f"⏰ <b>Напоминание о записи!</b>\n\n"
            f"Услуга: {service_name}\n"
            f"Дата: {date_long}\n"
            f"Время: {time_str}\n\n"
            f"Жду тебя! 💆‍♀️",
        )
    except Exception:
        pass  # Пользователь мог заблокировать бота


def cancel_reminder(booking_id: int) -> None:
    """Отменяет запланированное напоминание."""
    job_id = f"reminder_{booking_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
