"""LCUTC2-70: chống dò mật khẩu khi đăng nhập và yêu cầu mật khẩu mới đủ mạnh.

- Sai ``LOGIN_MAX_FAILED_ATTEMPTS`` lần trong cửa sổ đếm thì email bị tạm chặn,
  kể cả nhập đúng mật khẩu; email không tồn tại bị đối xử giống hệt.
- Đăng nhập đúng thì xoá bộ đếm; hết thời gian chặn thì đếm lại từ đầu.
- Mật khẩu mới: >= 8 ký tự, có chữ hoa, chữ số, ký tự đặc biệt, không chứa MSSV/email.
"""

from datetime import timedelta

import pytest
from sqlmodel import Session

from app.core import config
from app.core.exceptions import WeakPasswordError
from app.core.security.passwords import hash_password
from app.core.utils import datetime_utils
from app.models import LoginAttempt, User
from app.modules.auth import login_throttle
from app.modules.auth import service as svc
from app.modules.auth.login_throttle import LoginRateLimitedError
from app.modules.auth.schemas import ChangePasswordRequest, LoginRequest

PASSWORD = "Old-Password-123"
WRONG = "Wrong-Password-999"
EMAIL = "6451071234@st.utc2.edu.vn"


@pytest.fixture(autouse=True)
def thresholds(monkeypatch):
    monkeypatch.setattr(config, "LOGIN_MAX_FAILED_ATTEMPTS", 3)
    monkeypatch.setattr(config, "LOGIN_FAILURE_WINDOW_MINUTES", 15)
    monkeypatch.setattr(config, "LOGIN_LOCKOUT_MINUTES", 10)


@pytest.fixture
def clock(monkeypatch):
    """Đồng hồ giả cho login_throttle, tua được bằng ``clock.advance(minutes=...)``."""

    class Clock:
        now = datetime_utils.now_utc()

        def advance(self, **kwargs):
            self.now += timedelta(**kwargs)

    fake = Clock()
    monkeypatch.setattr(login_throttle, "now_utc", lambda: fake.now)
    return fake


@pytest.fixture
def user(session: Session) -> User:
    user = User(
        full_name="Sinh viên A",
        email=EMAIL,
        student_code="6451071234",
        hashed_password=hash_password(PASSWORD),
        role_id=3,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _login(session, password=PASSWORD, email=EMAIL):
    return svc.login(session, LoginRequest(email=email, password=password))


def _fail(session, times, email=EMAIL):
    for _ in range(times):
        with pytest.raises(svc.InvalidCredentialsError):
            _login(session, WRONG, email)


# ------------------------------------------------------------- brute-force
def test_reaching_limit_returns_429_on_that_attempt(session, user, clock):
    _fail(session, 2)

    with pytest.raises(LoginRateLimitedError) as exc:
        _login(session, WRONG)

    assert exc.value.status_code == 429
    assert exc.value.error_code == "LOGIN_RATE_LIMITED"
    assert exc.value.message == (
        "Bạn đã đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 10 phút"
    )


def test_locked_email_rejects_even_correct_password_without_checking_it(
    session, user, clock, monkeypatch
):
    _fail(session, 2)
    with pytest.raises(LoginRateLimitedError):
        _login(session, WRONG)
    calls = []
    monkeypatch.setattr(svc, "_safe_verify", lambda *a: calls.append(a) or True)
    clock.advance(minutes=3)

    with pytest.raises(LoginRateLimitedError) as exc:
        _login(session)

    assert calls == []
    assert "thử lại sau 7 phút" in exc.value.message


def test_lockout_expires_and_counter_starts_over(session, user, clock):
    _fail(session, 2)
    with pytest.raises(LoginRateLimitedError):
        _login(session, WRONG)
    clock.advance(minutes=10)

    # Hết chặn: lần sai kế tiếp chỉ là lần thứ 1 của lượt đếm mới
    _fail(session, 2)
    response, _ = _login(session)
    assert response.user.email == EMAIL


def test_successful_login_resets_counter(session, user, clock):
    _fail(session, 2)
    _login(session)

    assert session.get(LoginAttempt, EMAIL) is None
    _fail(session, 2)  # vẫn chưa chạm ngưỡng 3


def test_failures_outside_window_are_not_accumulated(session, user, clock):
    _fail(session, 2)
    clock.advance(minutes=15)

    _fail(session, 2)
    _login(session)


def test_unknown_email_is_throttled_exactly_like_existing_one(session, user, clock):
    unknown = "khongton@st.utc2.edu.vn"
    _fail(session, 2, email=unknown)

    with pytest.raises(LoginRateLimitedError) as exc:
        _login(session, WRONG, unknown)

    assert exc.value.message.startswith("Bạn đã đăng nhập sai quá nhiều lần")


def test_counter_key_matches_login_lookup_exactly(session, user, clock):
    """Login so khớp email chính xác (chỉ strip), nên bộ đếm cũng vậy.

    Email khác hoa/thường không bao giờ đăng nhập được vào tài khoản thật, nên
    đếm riêng không mở đường lách ngưỡng.
    """
    _fail(session, 2, email=EMAIL.upper())
    _fail(session, 2)

    response, _ = _login(session)
    assert response.user.email == EMAIL


def test_counter_is_per_email(session, user, clock):
    _fail(session, 2, email="khac@st.utc2.edu.vn")
    _fail(session, 2)

    response, _ = _login(session)
    assert response.user.email == EMAIL


def test_locked_account_with_correct_password_still_clears_counter(session, user, clock):
    user.is_active = False
    session.add(user)
    session.commit()
    _fail(session, 2)

    with pytest.raises(svc.AccountLockedError):
        _login(session)
    assert session.get(LoginAttempt, EMAIL) is None


# --------------------------------------------------------- password strength
@pytest.mark.parametrize(
    ("password", "message"),
    [
        ("Ab1!", "Mật khẩu mới phải có ít nhất 8 ký tự"),
        ("abcdef1!", "Mật khẩu mới cần ít nhất 1 chữ cái viết hoa"),
        ("Abcdefg!", "Mật khẩu mới cần ít nhất 1 chữ số"),
        ("Abcdefg1", "Mật khẩu mới cần ít nhất 1 ký tự đặc biệt"),
        ("Abcdef1 ", "Mật khẩu mới cần ít nhất 1 ký tự đặc biệt"),
    ],
)
def test_weak_new_password_is_rejected(password, message):
    # Validator raise thẳng AppError (handler toàn cục trả 422 WEAK_PASSWORD)
    with pytest.raises(WeakPasswordError) as exc:
        ChangePasswordRequest(
            current_password=PASSWORD, new_password=password, confirm_password=password
        )
    assert exc.value.message == message


@pytest.mark.parametrize("password", ["Abcdef1!", "Mk_2026.utc", "Xin-Chao-9"])
def test_strong_new_password_is_accepted(password):
    request = ChangePasswordRequest(
        current_password=PASSWORD, new_password=password, confirm_password=password
    )
    assert request.new_password == password


def test_login_keeps_accepting_old_weak_passwords():
    """Luật mới chỉ áp cho mật khẩu mới; tài khoản cũ vẫn đăng nhập được."""
    assert LoginRequest(email=EMAIL, password="abcdefgh").password == "abcdefgh"


@pytest.mark.parametrize("new", ["Mk@6451071234", "6451071234@Mk", "X1!6451071234"])
def test_new_password_containing_student_code_is_rejected(session, user, new):
    request = ChangePasswordRequest(
        current_password=PASSWORD, new_password=new, confirm_password=new
    )

    with pytest.raises(WeakPasswordError) as exc:
        svc.change_password(session, user, request)

    assert exc.value.status_code == 422
    assert exc.value.message == "Mật khẩu mới không được chứa mã sinh viên hoặc email"
    session.refresh(user)
    assert user.token_version == 0


def test_new_password_containing_email_name_is_rejected(session):
    teacher = User(
        full_name="Giáo viên B",
        email="NguyenVanB@utc2.edu.vn",
        hashed_password=hash_password(PASSWORD),
        role_id=2,
    )
    session.add(teacher)
    session.commit()
    new = "nguyenvanb@2026A"

    with pytest.raises(WeakPasswordError):
        svc.change_password(
            session,
            teacher,
            ChangePasswordRequest(current_password=PASSWORD, new_password=new, confirm_password=new),
        )
