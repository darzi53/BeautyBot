from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_booking_actions(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"adm_ok:{booking_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no:{booking_id}"),
        ]
    ])
