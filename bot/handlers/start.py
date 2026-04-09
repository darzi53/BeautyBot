from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User
from bot.keyboards.main_menu import get_main_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession) -> None:
    tg_user = message.from_user
    result = await session.execute(select(User).where(User.telegram_id == tg_user.id))
    user = result.scalar_one_or_none()
    if user is None:
        session.add(User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name or "Unknown",
        ))
        await session.commit()

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


@router.callback_query(lambda c: c.data == "book")
async def handle_book(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "📅 <b>Запись на приём</b>\n\n"
        "Функция записи скоро будет доступна. Следите за обновлениями!"
    )


@router.callback_query(lambda c: c.data == "services")
async def handle_services(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "💅 <b>Наши услуги</b>\n\n"
        "Маникюр, педикюр, наращивание ногтей и многое другое.\n"
        "Полный прайс-лист скоро появится здесь!"
    )


@router.callback_query(lambda c: c.data == "contacts")
async def handle_contacts(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "📞 <b>Контакты</b>\n\n"
        "Свяжитесь с нами для уточнения деталей.\n"
        "Контактная информация скоро будет добавлена."
    )
