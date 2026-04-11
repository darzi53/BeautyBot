from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256))
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    service_name: Mapped[str] = mapped_column(String(256))
    service_price: Mapped[int] = mapped_column(Integer)
    date: Mapped[str] = mapped_column(String(20))   # "2026-04-15"
    time: Mapped[str] = mapped_column(String(5))    # "14:00"
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # Статусы: pending | confirmed | cancelled | rejected
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="bookings")


class BlockedSlot(Base):
    __tablename__ = "blocked_slots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(20))   # "2026-04-15"
    time: Mapped[str] = mapped_column(String(5))    # "14:00"
