from datetime import datetime
from typing import TypedDict


class UserDoc(TypedDict, total=False):
    telegram_id: int
    username: str | None
    full_name: str
    phone_number: str | None
    created_at: datetime


class BookingDoc(TypedDict, total=False):
    user_id: str          # str(ObjectId) пользователя
    service_name: str
    service_price: int
    date: str             # "2026-04-15"
    time: str             # "14:00"
    status: str           # pending | confirmed | cancelled | rejected
    created_at: datetime


class BlockedSlotDoc(TypedDict, total=False):
    date: str
    time: str
