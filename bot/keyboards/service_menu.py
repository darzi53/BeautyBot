from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.constants import SERVICES


def get_service_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=svc["name"], callback_data=f"svc:{i}")]
        for i, svc in enumerate(SERVICES)
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
