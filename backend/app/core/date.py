from datetime import date

from app.core.exceptions import InvalidFormatError

INVALID_DATE_MESSAGE = "Ngày sinh lưu vào cơ sở dữ liệu phải có định dạng yyyy-mm-dd"


def build_date(day: int, month: int, year: int) -> date:
    is_leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_in_month = (
        31,
        29 if is_leap_year else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    )

    if year < 1 or year > 9999 or month < 1 or month > 12:
        raise InvalidFormatError(INVALID_DATE_MESSAGE)
    if day < 1 or day > days_in_month[month - 1]:
        raise InvalidFormatError(INVALID_DATE_MESSAGE)

    return date(year, month, day)


def age_calculation(day: int, month: int, year: int) -> int:
    birth_date = build_date(day, month, year)

    today = date.today()

    age = today.year - birth_date.year

    # Năm nay chưa đến sinh nhật
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age
