from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.date_utils import date_to_str, format_date


def get_date_picker(dates: list[date]) -> InlineKeyboardMarkup:
    # По 3 кнопки в ряд
    rows = []
    row = []
    for d in dates:
        row.append(
            InlineKeyboardButton(
                text=format_date(d),
                callback_data=f"date:{date_to_str(d)}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_services")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
