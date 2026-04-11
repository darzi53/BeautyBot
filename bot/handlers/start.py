from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Contact,
    FSInputFile,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User
from bot.keyboards.main_menu import get_main_menu
from bot.states import RegistrationStates
from bot.utils.slot_utils import has_active_booking

router = Router()

PRICE_IMAGE = FSInputFile("bot/img/price.jpg")


async def _get_or_create_user(session: AsyncSession, tg_user) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == tg_user.id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name or "Unknown",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def send_main_menu(target: Message | CallbackQuery, session: AsyncSession, user: User) -> None:
    """Отправляет главное меню с учётом роли и активных записей."""
    is_admin = user.telegram_id in settings.ADMIN_IDS
    active = await has_active_booking(session, user.id)
    text = "Главное меню — выбери нужное 👇"
    markup = get_main_menu(is_admin=is_admin, has_active=active)

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    tg_user = message.from_user
    user = await _get_or_create_user(session, tg_user)

    if not user.phone_number:
        await state.set_state(RegistrationStates.waiting_for_phone)
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            f"💆‍♀️ Привет, {tg_user.first_name}!\n\n"
            "Добро пожаловать — я помогу тебе записаться к мастеру.\n\n"
            "Для начала поделись своим номером телефона 👇",
            reply_markup=kb,
        )
    else:
        await message.answer(
            f"💆‍♀️ Привет, {tg_user.first_name}!\n\n"
            "Добро пожаловать — я помогу тебе записаться к мастеру.\n\n"
            "Выбирай, что тебя интересует 👇",
            reply_markup=ReplyKeyboardRemove(),
        )
        await send_main_menu(message, session, user)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def handle_contact(message: Message, session: AsyncSession, state: FSMContext) -> None:
    contact: Contact = message.contact
    await _save_phone(message, session, state, contact.phone_number)


@router.message(RegistrationStates.waiting_for_phone, F.text)
async def handle_phone_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    phone = message.text.strip()
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 7:
        await message.answer("Пожалуйста, введи корректный номер телефона.")
        return
    await _save_phone(message, session, state, phone)


async def _save_phone(message: Message, session: AsyncSession, state: FSMContext, phone: str) -> None:
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.phone_number = phone
        await session.commit()

    await state.clear()
    await message.answer(
        "✅ Номер сохранён!\n\nВыбирай, что тебя интересует 👇",
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_main_menu(message, session, user)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/start — главное меню\n"
        "/help — эта справка"
    )


@router.callback_query(F.data == "prices")
async def handle_prices(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer_photo(
        photo=PRICE_IMAGE,
        caption="💰 Актуальный прайс-лист",
    )


@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    if user:
        await send_main_menu(callback, session, user)
