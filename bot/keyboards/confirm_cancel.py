from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_confirm_cancel(booking_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, отменить", callback_data=f"yes_cancel:{booking_id}"),
            InlineKeyboardButton(text="🔙 Нет, оставить", callback_data="no_cancel"),
        ]
    ])
