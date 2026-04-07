from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import get_main_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await message.answer(
        "Привет! Добро пожаловать в BeautyBot 💅\n\n"
        "Я помогу вам записаться к мастеру, узнать об услугах и ценах.",
        reply_markup=get_main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/start — главное меню\n"
        "/help — эта справка"
    )
