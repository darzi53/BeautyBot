from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(lambda c: c.data == "admin_panel")
async def handle_admin_panel(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("⚙️ <b>Админ панель</b>\n\nВ разработке.")
