from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings


def get_main_menu(is_admin: bool = False, has_active: bool = False) -> InlineKeyboardMarkup:
    if has_active:
        # Есть активная запись — две кнопки в первом ряду
        row1 = [
            InlineKeyboardButton(text="📅 Записаться", callback_data="book"),
            InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_booking"),
        ]
    else:
        # Нет активной записи — кнопка Записаться на всю ширину
        row1 = [
            InlineKeyboardButton(text="📅 Записаться", callback_data="book"),
        ]

    buttons = [
        row1,
        [
            InlineKeyboardButton(text="💰 Прайсы", callback_data="prices"),
            InlineKeyboardButton(text="🖼 Портфолио", url=settings.PORTFOLIO_URL),
        ],
    ]

    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="⚙️ Админ панель", callback_data="admin_panel"),
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
