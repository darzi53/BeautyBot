from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_time_picker(slots: list[str]) -> InlineKeyboardMarkup:
    # По 3 кнопки в ряд
    rows = []
    row = []
    for slot in slots:
        row.append(
            InlineKeyboardButton(text=slot, callback_data=f"time:{slot}")
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_dates")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
