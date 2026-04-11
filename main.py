import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.engine import connect_db, create_indexes, close_db
from bot.handlers import admin, common, start
from bot.handlers import booking, cancellation
from bot.middlewares.db import DbMiddleware
from bot.utils.reminder import scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    await connect_db()
    await create_indexes()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.middleware(DbMiddleware())

    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(cancellation.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)  # всегда последний

    scheduler.start()
    logging.info("APScheduler запущен (Asia/Tashkent)")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
