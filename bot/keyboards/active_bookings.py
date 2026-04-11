from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.date_utils import str_to_date, format_date_long


def get_active_bookings_menu(bookings: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for b in bookings:
        date_label = format_date_long(str_to_date(b["date"]))
        label = f"📅 {date_label}, {b['time']} — {b['service_name']}"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"cancel_id:{b['_id']}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
