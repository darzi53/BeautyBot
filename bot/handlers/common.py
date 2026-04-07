from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Не понимаю эту команду. Используй /help для справки.")
