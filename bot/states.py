from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_phone = State()


class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirming = State()


class CancelStates(StatesGroup):
    choosing_booking = State()
    confirming_cancel = State()


class AdminSlotStates(StatesGroup):
    choosing_action = State()   # block | unblock
    choosing_date = State()
    choosing_time = State()
