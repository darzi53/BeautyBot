import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.engine import create_tables
from bot.handlers import admin, common, start
from bot.handlers import booking, cancellation
from bot.middlewares.db import DbSessionMiddleware
from bot.utils.reminder import scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    await create_tables()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.middleware(DbSessionMiddleware())

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


if __name__ == "__main__":
    asyncio.run(main())
