from datetime import date


def is_at_least_17(day: int, month: int, year: int) -> bool:
    try:
        birth_date = date(year, month, day)
    except ValueError:
        return False  # ngày sinh không hợp lệ

    today = date.today()

    age = today.year - birth_date.year

    # Năm nay chưa đến sinh nhật
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age >= 17

def is_at_least_22(day: int, month: int, year: int) -> bool:
    try:
        birth_date = date(year, month, day)
    except ValueError:
        return False  # ngày sinh không hợp lệ

    today = date.today()

    age = today.year - birth_date.year

    # Năm nay chưa đến sinh nhật
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age >= 22
