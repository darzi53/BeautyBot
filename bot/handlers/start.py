from datetime import datetime, timezone

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
from motor.motor_asyncio import AsyncIOMotorDatabase

from bot.config import settings
from bot.keyboards.main_menu import get_main_menu
from bot.states import RegistrationStates
from bot.utils.slot_utils import has_active_booking

router = Router()

PRICE_IMAGE = FSInputFile("bot/img/price.jpg")


async def _get_or_create_user(db: AsyncIOMotorDatabase, tg_user) -> dict:
    user = await db.users.find_one({"telegram_id": tg_user.id})
    if user is None:
        result = await db.users.insert_one({
            "telegram_id": tg_user.id,
            "username": tg_user.username,
            "full_name": tg_user.full_name or "Unknown",
            "phone_number": None,
            "created_at": datetime.now(timezone.utc),
        })
        user = await db.users.find_one({"_id": result.inserted_id})
    return user


async def send_main_menu(target: Message | CallbackQuery, db: AsyncIOMotorDatabase, user: dict) -> None:
    """Отправляет главное меню с учётом роли и активных записей."""
    is_admin = user["telegram_id"] in settings.ADMIN_IDS
    active = await has_active_booking(db, str(user["_id"]))
    text = "Главное меню — выбери нужное 👇"
    markup = get_main_menu(is_admin=is_admin, has_active=active)

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.message(Command("start"))
async def cmd_start(message: Message, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    await state.clear()
    tg_user = message.from_user
    user = await _get_or_create_user(db, tg_user)

    if not user.get("phone_number"):
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
        await send_main_menu(message, db, user)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def handle_contact(message: Message, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    contact: Contact = message.contact
    await _save_phone(message, db, state, contact.phone_number)


@router.message(RegistrationStates.waiting_for_phone, F.text)
async def handle_phone_text(message: Message, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    phone = message.text.strip()
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 7:
        await message.answer("Пожалуйста, введи корректный номер телефона.")
        return
    await _save_phone(message, db, state, phone)


async def _save_phone(message: Message, db: AsyncIOMotorDatabase, state: FSMContext, phone: str) -> None:
    await db.users.update_one(
        {"telegram_id": message.from_user.id},
        {"$set": {"phone_number": phone}},
    )
    user = await db.users.find_one({"telegram_id": message.from_user.id})

    await state.clear()
    await message.answer(
        "✅ Номер сохранён!\n\nВыбирай, что тебя интересует 👇",
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_main_menu(message, db, user)


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
async def handle_back_to_main(callback: CallbackQuery, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    user = await db.users.find_one({"telegram_id": callback.from_user.id})
    if user:
        await send_main_menu(callback, db, user)
