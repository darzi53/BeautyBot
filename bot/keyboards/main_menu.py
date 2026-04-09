from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings


def get_main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📝 Записаться", callback_data="book"),
            InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_booking"),
        ],
        [
            InlineKeyboardButton(text="💰 Прайсы", url=settings.REVIEWS_URL),
            InlineKeyboardButton(text="🖼 Портфолио", url=settings.PORTFOLIO_URL),
        ],
    ]
    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="⚙️ Админ панель", callback_data="admin_panel"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
