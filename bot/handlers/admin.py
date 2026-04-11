from aiogram import F, Router
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import BlockedSlot, Booking, User
from bot.states import AdminSlotStates
from bot.utils.date_utils import (
    format_date,
    format_date_long,
    get_available_dates,
    str_to_date,
)

router = Router()


class IsAdmin(Filter):
    async def __call__(self, event: CallbackQuery | Message) -> bool:
        user_id = event.from_user.id
        return user_id in settings.ADMIN_IDS


# ─── Главная панель ────────────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data == "admin_panel")
async def handle_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "⚙️ <b>Админ панель</b>\n\nВыбери действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Записи", callback_data="adm_list")],
            [InlineKeyboardButton(text="🔒 Управление слотами", callback_data="adm_slots")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")],
        ]),
    )


# ─── Подтверждение / отклонение записи ────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("adm_ok:"))
async def handle_adm_ok(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    booking_id = int(callback.data.split(":")[1])

    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        await callback.message.edit_text("⚠️ Запись не найдена.")
        return

    booking.status = "confirmed"
    await session.commit()

    # Получаем telegram_id пользователя
    user_result = await session.execute(select(User).where(User.id == booking.user_id))
    user = user_result.scalar_one_or_none()

    date_label = format_date_long(str_to_date(booking.date))

    # Редактируем сообщение у админа
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Подтверждено</b>",
    )

    # Уведомляем клиента
    if user:
        try:
            await callback.bot.send_message(
                user.telegram_id,
                f"🎉 Запись подтверждена!\n\n"
                f"Услуга: {booking.service_name}\n"
                f"Дата: {date_label}, {booking.time}\n\n"
                "Жду тебя! Если планы изменятся — можешь отменить запись через меню.",
            )
        except Exception:
            pass


@router.callback_query(IsAdmin(), F.data.startswith("adm_no:"))
async def handle_adm_no(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    booking_id = int(callback.data.split(":")[1])

    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        await callback.message.edit_text("⚠️ Запись не найдена.")
        return

    booking.status = "rejected"
    await session.commit()

    user_result = await session.execute(select(User).where(User.id == booking.user_id))
    user = user_result.scalar_one_or_none()

    # Отменяем напоминание
    from bot.utils.reminder import cancel_reminder
    cancel_reminder(booking_id)

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <b>Отклонено</b>",
    )

    if user:
        try:
            await callback.bot.send_message(
                user.telegram_id,
                "😔 К сожалению, мастер не смог подтвердить запись на это время.\n\n"
                "Попробуй выбрать другую дату или время через меню.",
            )
        except Exception:
            pass


# ─── Список записей (Админ) ────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data == "adm_list")
async def handle_adm_list(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    result = await session.execute(
        select(Booking, User)
        .join(User, Booking.user_id == User.id)
        .where(Booking.status.in_(["pending", "confirmed"]))
        .order_by(Booking.date, Booking.time)
    )
    rows = result.fetchall()

    if not rows:
        await callback.message.answer(
            "📋 Активных записей нет.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
            ]),
        )
        return

    lines = ["📋 <b>Активные записи:</b>\n"]
    for booking, user in rows:
        date_label = format_date_long(str_to_date(booking.date))
        status_icon = "⏳" if booking.status == "pending" else "✅"
        username = f"@{user.username}" if user.username else user.full_name
        lines.append(
            f"{status_icon} <b>{date_label}, {booking.time}</b>\n"
            f"   {booking.service_name}\n"
            f"   {username} · {user.phone_number or 'нет тел.'}\n"
        )

    await callback.message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]),
    )


# ─── Управление слотами (Админ) ────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data == "adm_slots")
async def handle_adm_slots(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminSlotStates.choosing_action)
    await callback.message.answer(
        "🔒 Управление слотами\n\nЧто хочешь сделать?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Заблокировать слот", callback_data="slot_block")],
            [InlineKeyboardButton(text="✅ Разблокировать слот", callback_data="slot_unblock")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")],
        ]),
    )


@router.callback_query(AdminSlotStates.choosing_action, F.data.in_({"slot_block", "slot_unblock"}))
async def handle_slot_action(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    action = "block" if callback.data == "slot_block" else "unblock"
    await state.update_data(slot_action=action)
    await state.set_state(AdminSlotStates.choosing_date)

    dates = get_available_dates()
    buttons = [
        [InlineKeyboardButton(text=format_date(d), callback_data=f"slot_date:{d.isoformat()}")]
        for d in dates
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="adm_slots")])

    verb = "заблокировать" if action == "block" else "разблокировать"
    await callback.message.answer(
        f"Выбери дату ({verb}):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(AdminSlotStates.choosing_date, F.data.startswith("slot_date:"))
async def handle_slot_date(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    date_str = callback.data.split(":", 1)[1]
    await state.update_data(slot_date=date_str)
    await state.set_state(AdminSlotStates.choosing_time)

    from bot.constants import TIME_SLOTS
    buttons = [
        [InlineKeyboardButton(text=t, callback_data=f"slot_time:{t}")]
        for t in TIME_SLOTS
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="adm_slots")])

    date_label = format_date_long(str_to_date(date_str))
    await callback.message.answer(
        f"Выбери время ({date_label}):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(AdminSlotStates.choosing_time, F.data.startswith("slot_time:"))
async def handle_slot_time(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await callback.answer()
    time_str = callback.data.split(":", 1)[1]
    data = await state.get_data()
    date_str = data["slot_date"]
    action = data["slot_action"]
    await state.clear()

    date_label = format_date_long(str_to_date(date_str))

    if action == "block":
        # Проверяем — нет ли уже
        existing = await session.execute(
            select(BlockedSlot).where(
                BlockedSlot.date == date_str, BlockedSlot.time == time_str
            )
        )
        if not existing.scalar_one_or_none():
            session.add(BlockedSlot(date=date_str, time=time_str))
            await session.commit()
        await callback.message.answer(
            f"🚫 Слот заблокирован: {date_label}, {time_str}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К управлению слотами", callback_data="adm_slots")]
            ]),
        )
    else:
        result = await session.execute(
            select(BlockedSlot).where(
                BlockedSlot.date == date_str, BlockedSlot.time == time_str
            )
        )
        slot = result.scalar_one_or_none()
        if slot:
            await session.delete(slot)
            await session.commit()
            await callback.message.answer(
                f"✅ Слот разблокирован: {date_label}, {time_str}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К управлению слотами", callback_data="adm_slots")]
                ]),
            )
        else:
            await callback.message.answer(
                f"Слот {date_label}, {time_str} не был заблокирован.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К управлению слотами", callback_data="adm_slots")]
                ]),
            )
