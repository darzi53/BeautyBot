from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from bot.keyboards.active_bookings import get_active_bookings_menu
from bot.keyboards.confirm_cancel import get_confirm_cancel
from bot.states import CancelStates
from bot.utils.date_utils import format_date_long, str_to_date
from bot.utils.reminder import cancel_reminder
from bot.utils.slot_utils import get_user_active_bookings

router = Router()


@router.callback_query(F.data == "cancel_booking")
async def handle_cancel_booking(callback: CallbackQuery, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    user = await db.users.find_one({"telegram_id": callback.from_user.id})
    if not user:
        await callback.message.answer("Что-то пошло не так. Попробуй /start заново.")
        return

    bookings = await get_user_active_bookings(db, str(user["_id"]))

    if not bookings:
        await callback.message.answer(
            "У тебя пока нет активных записей.",
            reply_markup=_back_to_main_kb(),
        )
        return

    await state.set_state(CancelStates.choosing_booking)
    await callback.message.answer(
        "❌ Твои активные записи:",
        reply_markup=get_active_bookings_menu(bookings),
    )


@router.callback_query(CancelStates.choosing_booking, F.data.startswith("cancel_id:"))
async def handle_cancel_id(callback: CallbackQuery, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    await callback.answer()
    booking_id_str = callback.data.split(":")[1]

    booking = await db.bookings.find_one({"_id": ObjectId(booking_id_str)})
    if not booking or booking["status"] not in ("pending", "confirmed"):
        await callback.message.answer("Запись не найдена или уже отменена.")
        return

    await state.set_state(CancelStates.confirming_cancel)
    date_label = format_date_long(str_to_date(booking["date"]))

    await callback.message.answer(
        f"Отменить запись?\n\n"
        f"Услуга: {booking['service_name']}\n"
        f"Дата: {date_label}\n"
        f"Время: {booking['time']}",
        reply_markup=get_confirm_cancel(booking_id_str),
    )


@router.callback_query(CancelStates.confirming_cancel, F.data.startswith("yes_cancel:"))
async def handle_yes_cancel(callback: CallbackQuery, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    await callback.answer()
    booking_id_str = callback.data.split(":")[1]

    booking = await db.bookings.find_one({"_id": ObjectId(booking_id_str)})
    if not booking:
        await callback.message.answer("Запись не найдена.")
        await state.clear()
        return

    service_name = booking["service_name"]
    date_label = format_date_long(str_to_date(booking["date"]))
    time_str = booking["time"]

    await db.bookings.update_one(
        {"_id": ObjectId(booking_id_str)},
        {"$set": {"status": "cancelled"}},
    )
    await state.clear()

    cancel_reminder(booking_id_str)

    await callback.message.answer(
        f"Запись отменена ✅\n\n"
        f"Услуга: {service_name}\n"
        f"Дата: {date_label}\n"
        f"Время: {time_str}\n\n"
        f"Буду ждать тебя в следующий раз 💆‍♀️"
    )

    user = await db.users.find_one({"telegram_id": callback.from_user.id})
    if user:
        from bot.handlers.start import send_main_menu
        await send_main_menu(callback, db, user)


@router.callback_query(F.data == "no_cancel")
async def handle_no_cancel(callback: CallbackQuery, db: AsyncIOMotorDatabase, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    user = await db.users.find_one({"telegram_id": callback.from_user.id})
    if user:
        from bot.handlers.start import send_main_menu
        await send_main_menu(callback, db, user)


def _back_to_main_kb():
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
