from datetime import date


def age_calculation(day: int, month: int, year: int) -> int:
    try:
        birth_date = date(year, month, day)
    except ValueError:
        return 0  # ngày sinh không hợp lệ

    today = date.today()

    age = today.year - birth_date.year

    # Năm nay chưa đến sinh nhật
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age
