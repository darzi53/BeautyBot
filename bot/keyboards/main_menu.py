from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="💅 Услуги", callback_data="services")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
