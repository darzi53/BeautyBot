from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_confirm_booking() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_book"),
            InlineKeyboardButton(text="🔙 Изменить", callback_data="change_book"),
        ]
    ])
