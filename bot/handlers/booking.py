from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from motor.motor_asyncio import AsyncIOMotorDatabase

from bot.config import settings
from bot.constants import SERVICES
from bot.keyboards.admin_booking import get_admin_booking_actions
from bot.keyboards.confirm_booking import get_confirm_booking
from bot.keyboards.date_picker import get_date_picker
from bot.keyboards.service_menu import get_service_menu
from bot.keyboards.time_picker import get_time_picker
from bot.states import BookingStates
from bot.utils.date_utils import (
    format_date_long,
    get_available_dates,
    str_to_date,
)
from bot.utils.reminder import schedule_reminder
from bot.utils.slot_utils import get_free_slots, has_active_booking

router = Router()


@router.callback_query(F.data == "book")
async def handle_book(callback: CallbackQuery, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    await callback.answer()

    user = await db.users.find_one({"telegram_id": callback.from_user.id})
    if not user:
        await callback.message.answer("Что-то пошло не так. Попробуй /start заново.")
        return

    if await has_active_booking(db, str(user["_id"])):
        await callback.message.answer(
            "📅 У тебя уже есть активная запись!\n\n"
            "Дождись её завершения или отмени через меню."
        )
        return

    await state.set_state(BookingStates.choosing_service)
    await callback.message.answer(
        "🤨 Выбери услугу:",
        reply_markup=get_service_menu(),
    )


@router.callback_query(BookingStates.choosing_service, F.data.startswith("svc:"))
async def handle_service_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    idx = int(callback.data.split(":")[1])
    service = SERVICES[idx]

    await state.update_data(service_name=service["name"], service_price=service["price"])
    await state.set_state(BookingStates.choosing_date)

    dates = get_available_dates()
    if not dates:
        await callback.message.answer("Свободных дат пока нет. Загляни позже или напиши напрямую.")
        return

    await callback.message.answer(
        "📅 Выбери удобную дату:",
        reply_markup=get_date_picker(dates),
    )


@router.callback_query(BookingStates.choosing_service, F.data == "back_to_main")
async def handle_back_from_services(callback: CallbackQuery, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    from bot.handlers.start import send_main_menu
    await state.clear()
    await callback.answer()
    user = await db.users.find_one({"telegram_id": callback.from_user.id})
    if user:
        await send_main_menu(callback, db, user)


@router.callback_query(BookingStates.choosing_date, F.data.startswith("date:"))
async def handle_date_chosen(callback: CallbackQuery, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    await callback.answer()
    date_str = callback.data.split(":", 1)[1]

    free_slots = await get_free_slots(db, date_str)
    if not free_slots:
        await callback.message.answer(
            "К сожалению, на эту дату нет свободных слотов. Выбери другую дату 👇",
            reply_markup=get_date_picker(get_available_dates()),
        )
        return

    await state.update_data(date=date_str)
    await state.set_state(BookingStates.choosing_time)

    date_label = format_date_long(str_to_date(date_str))
    await callback.message.answer(
        f"⏰ Выбери время:\n📅 {date_label}",
        reply_markup=get_time_picker(free_slots),
    )


@router.callback_query(BookingStates.choosing_date, F.data == "back_to_services")
async def handle_back_to_services_from_date(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(BookingStates.choosing_service)
    await callback.message.answer(
        "🤨 Выбери услугу:",
        reply_markup=get_service_menu(),
    )


@router.callback_query(BookingStates.choosing_time, F.data.startswith("time:"))
async def handle_time_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    time_str = callback.data.split(":", 1)[1]
    await state.update_data(time=time_str)
    await state.set_state(BookingStates.confirming)

    data = await state.get_data()
    date_label = format_date_long(str_to_date(data["date"]))

    await callback.message.answer(
        f"📝 Проверь детали записи:\n\n"
        f"Услуга: {data['service_name']}\n"
        f"Дата: {date_label}\n"
        f"Время: {time_str}\n\n"
        f"Всё верно?",
        reply_markup=get_confirm_booking(),
    )


@router.callback_query(BookingStates.choosing_time, F.data == "back_to_dates")
async def handle_back_to_dates(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(BookingStates.choosing_date)
    await callback.message.answer(
        "📅 Выбери удобную дату:",
        reply_markup=get_date_picker(get_available_dates()),
    )


@router.callback_query(BookingStates.confirming, F.data == "confirm_book")
async def handle_confirm_booking(
    callback: CallbackQuery,
    db: AsyncIOMotorDatabase,
    state: FSMContext,
) -> None:
    await callback.answer()
    data = await state.get_data()
    await state.clear()

    user = await db.users.find_one({"telegram_id": callback.from_user.id})
    if not user:
        await callback.message.answer("Что-то пошло не так. Попробуй /start заново.")
        return

    result = await db.bookings.insert_one({
        "user_id": str(user["_id"]),
        "service_name": data["service_name"],
        "service_price": data["service_price"],
        "date": data["date"],
        "time": data["time"],
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    })
    booking_id_str = str(result.inserted_id)

    date_label = format_date_long(str_to_date(data["date"]))

    await callback.message.answer(
        "⏳ Заявка отправлена!\n\n"
        f"Услуга: {data['service_name']}\n"
        f"Дата: {date_label}\n"
        f"Время: {data['time']}\n\n"
        "Жди подтверждения от мастера 💆‍♀️"
    )

    username = f"@{user['username']}" if user.get("username") else "нет username"
    phone = user.get("phone_number") or "не указан"
    admin_text = (
        f"📅 Новая заявка на запись!\n\n"
        f"👤 Клиент: {user['full_name']} ({username})\n"
        f"💬 Telegram ID: {user['telegram_id']}\n"
        f"📞 Телефон: {phone}\n"
        f"Услуга: {data['service_name']}\n"
        f"Дата: {date_label}\n"
        f"Время: {data['time']}"
    )

    bot = callback.bot
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=get_admin_booking_actions(booking_id_str),
            )
        except Exception:
            pass

    await schedule_reminder(
        bot=bot,
        booking_id=booking_id_str,
        date_str=data["date"],
        time_str=data["time"],
        user_telegram_id=user["telegram_id"],
        service_name=data["service_name"],
        date_long=date_label,
    )

    from bot.handlers.start import send_main_menu
    await send_main_menu(callback, db, user)


@router.callback_query(BookingStates.confirming, F.data == "change_book")
async def handle_change_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(BookingStates.choosing_date)
    await callback.message.answer(
        "📅 Выбери другую дату:",
        reply_markup=get_date_picker(get_available_dates()),
    )
