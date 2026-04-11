from datetime import date, timedelta

MONTHS_RU = {
    1: "янв", 2: "фев", 3: "мар", 4: "апр",
    5: "май", 6: "июн", 7: "июл", 8: "авг",
    9: "сен", 10: "окт", 11: "ноя", 12: "дек",
}

MONTHS_RU_FULL = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

WEEKDAYS_RU = {
    0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс",
}

WEEKDAYS_RU_FULL = {
    0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "вс",
}


def get_available_dates() -> list[date]:
    """Возвращает список доступных дат — 7 рабочих дней вперёд (пн–сб, без воскресенья)."""
    result = []
    current = date.today() + timedelta(days=1)
    while len(result) < 7:
        if current.weekday() != 6:  # 6 = воскресенье
            result.append(current)
        current += timedelta(days=1)
    return result


def format_date(d: date) -> str:
    """Короткий формат для кнопок: 'Пн 14 апр'."""
    return f"{WEEKDAYS_RU[d.weekday()]} {d.day} {MONTHS_RU[d.month]}"


def format_date_long(d: date) -> str:
    """Длинный формат для сообщений: '14 апреля (пн)'."""
    return f"{d.day} {MONTHS_RU_FULL[d.month]} ({WEEKDAYS_RU_FULL[d.weekday()]})"


def date_to_str(d: date) -> str:
    """ISO-формат для хранения в БД: '2026-04-15'."""
    return d.isoformat()


def str_to_date(s: str) -> date:
    """Парсинг ISO-строки из БД."""
    return date.fromisoformat(s)
