"""LCUTC2-70: chống dò mật khẩu khi đăng nhập và yêu cầu mật khẩu mới đủ mạnh.

- Sai ``LOGIN_MAX_FAILED_ATTEMPTS`` lần trong cửa sổ đếm thì email bị tạm chặn,
  kể cả nhập đúng mật khẩu; email không tồn tại bị đối xử giống hệt.
- Đăng nhập đúng thì xoá bộ đếm; hết thời gian chặn thì đếm lại từ đầu.
- Mật khẩu mới: >= 8 ký tự, có chữ hoa, chữ số, ký tự đặc biệt, không chứa MSSV/email.
"""

from datetime import timedelta

import pytest
from sqlalchemy import Insert, delete
from sqlmodel import Session, select

from app.core import config
from app.core.exceptions import WeakPasswordError
from app.core.security.passwords import hash_password
from app.core.utils import datetime_utils
from app.models import LoginAttempt, User
from app.modules.auth import login_throttle
from app.modules.auth import service as svc
from app.modules.auth.login_throttle import LoginRateLimitedError, LoginUnavailableError
from app.modules.auth.schemas import ChangePasswordRequest, LoginRequest
from app.modules.users import service as users_svc

PASSWORD = "Old-Password-123"
WRONG = "Wrong-Password-999"
EMAIL = "6451071234@st.utc2.edu.vn"


@pytest.fixture(autouse=True)
def thresholds(monkeypatch):
    monkeypatch.setattr(config, "LOGIN_MAX_FAILED_ATTEMPTS", 3)
    monkeypatch.setattr(config, "LOGIN_FAILURE_WINDOW_MINUTES", 15)
    monkeypatch.setattr(config, "LOGIN_LOCKOUT_MINUTES", 10)
    # Lượt đăng nhập đầu tiên của mỗi test luôn chạy dọn dẹp
    monkeypatch.setattr(login_throttle, "_last_purge", None)


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


def test_locked_account_with_correct_password_keeps_counting(session, user, clock):
    """Đoán trúng mật khẩu của tài khoản bị khoá không được xoá bộ đếm."""
    user.is_active = False
    session.add(user)
    session.commit()
    _fail(session, 1)

    with pytest.raises(svc.AccountLockedError):
        _login(session)
    assert session.get(LoginAttempt, EMAIL).failed_count == 2

    # Lượt chạm ngưỡng trả 429 như mọi lượt sai, kể cả khi mật khẩu đúng
    with pytest.raises(LoginRateLimitedError):
        _login(session)


@pytest.fixture
def admin(session: Session) -> User:
    admin = User(
        full_name="Quản trị viên",
        email="quantri@st.utc2.edu.vn",
        hashed_password=hash_password(PASSWORD),
        role_id=1,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


def test_reset_password_clears_counter(session, user, admin, clock):
    """Được đặt lại mật khẩu thì đăng nhập được ngay bằng mật khẩu tạm, không còn 429."""
    _fail(session, 2)
    with pytest.raises(LoginRateLimitedError):
        _login(session, WRONG)

    users_svc.reset_password(session, admin, user.user_id)

    response, _ = _login(session, user.student_code)
    assert response.user.must_change_password is True


def test_unlock_clears_counter(session, user, admin, clock):
    """Lúc bị khoá, nhập đúng mật khẩu vẫn tính lượt sai; mở khoá thì phải xoá bộ đếm."""
    users_svc.lock_user(session, admin, user.user_id)
    for _ in range(2):
        with pytest.raises(svc.AccountLockedError):
            _login(session)
    with pytest.raises(LoginRateLimitedError):
        _login(session)

    users_svc.unlock_user(session, admin, user.user_id)

    response, _ = _login(session)
    assert response.user.email == EMAIL


def test_login_response_includes_student_code(session, user, admin, clock):
    """FE cần MSSV để báo trước luật "không chứa MSSV" (email không phải lúc nào cũng là MSSV)."""
    response, _ = _login(session)
    assert response.user.student_code == "6451071234"
    response, _ = _login(session, email=admin.email)
    assert response.user.student_code is None


# ------------------------------------------------------------- concurrency
def test_counter_is_reread_under_lock_not_taken_from_session_cache(
    engine, session, user, clock
):
    """Object cũ trong identity map không được ghi đè bộ đếm mới hơn của request khác."""
    _fail(session, 1)
    cached = session.get(LoginAttempt, EMAIL)
    assert cached.failed_count == 1
    with Session(engine) as other:  # một request khác sai thêm lần nữa
        _fail(other, 1)

    # Đây là lần sai thứ 3 = ngưỡng, không phải "1 + 1" từ giá trị cũ trong cache
    with pytest.raises(LoginRateLimitedError):
        _login(session, WRONG)
    assert session.get(LoginAttempt, EMAIL).failed_count == 3


def test_parallel_request_during_last_attempt_is_rejected_without_checking_password(
    engine, session, user, clock, monkeypatch
):
    """Lượt cuối được giữ chỗ trước bcrypt: request song song nhận 429 ngay."""
    _fail(session, 2)
    real_verify = svc._safe_verify
    calls = []

    def verify(password, hashed):
        calls.append(password)
        if len(calls) == 1:
            # Request song song tới đúng lúc lượt cuối đang chạy bcrypt, kể cả đoán đúng
            with Session(engine) as other, pytest.raises(LoginRateLimitedError):
                _login(other)
        return real_verify(password, hashed)

    monkeypatch.setattr(svc, "_safe_verify", verify)

    with pytest.raises(LoginRateLimitedError):
        _login(session, WRONG)
    assert calls == [WRONG]


def test_attempt_is_never_silently_skipped(session, user, clock, monkeypatch):
    """Không giữ chỗ được (dòng luôn bị xoá ngay sau khi tạo) thì dừng, không thử mật khẩu."""
    real_exec = session.exec

    def exec_then_delete(statement, *args, **kwargs):
        result = real_exec(statement, *args, **kwargs)
        if isinstance(statement, Insert):
            real_exec(delete(LoginAttempt))  # đăng nhập đúng ở request khác chen vào
        return result

    monkeypatch.setattr(session, "exec", exec_then_delete)
    monkeypatch.setattr(svc, "_safe_verify", lambda *a: pytest.fail("không được kiểm tra mật khẩu"))

    with pytest.raises(LoginUnavailableError):
        _login(session, WRONG)


# ---------------------------------------------------------------- cleanup
def _stored_emails(session):
    return sorted(session.exec(select(LoginAttempt.email)).all())


def test_expired_rows_are_purged(session, user, clock):
    abandoned = "bo-di@st.utc2.edu.vn"
    blocked = "bi-chan@st.utc2.edu.vn"
    _fail(session, 1, email=abandoned)  # sai một lần rồi không quay lại
    _fail(session, 2, email=blocked)
    with pytest.raises(LoginRateLimitedError):
        _login(session, WRONG, blocked)
    assert _stored_emails(session) == [blocked, abandoned]

    clock.advance(minutes=15)  # hết cửa sổ đếm và hết thời gian chặn (10 phút)
    _fail(session, 1)

    assert _stored_emails(session) == [EMAIL]


def test_purge_keeps_rows_that_are_still_blocked(session, user, clock, monkeypatch):
    monkeypatch.setattr(config, "LOGIN_LOCKOUT_MINUTES", 30)
    _fail(session, 2)
    with pytest.raises(LoginRateLimitedError):
        _login(session, WRONG)

    clock.advance(minutes=20)  # hết cửa sổ đếm nhưng vẫn còn bị chặn
    _fail(session, 1, email="khac@st.utc2.edu.vn")

    assert EMAIL in _stored_emails(session)
    with pytest.raises(LoginRateLimitedError) as exc:
        _login(session)
    assert "thử lại sau 10 phút" in exc.value.message


# --------------------------------------------------------- password strength
@pytest.mark.parametrize(
    ("password", "message"),
    [
        ("Ab1!", "Mật khẩu mới phải có ít nhất 8 ký tự"),
        ("abcdef1!", "Mật khẩu mới cần ít nhất 1 chữ cái viết hoa"),
        ("Abcdefg!", "Mật khẩu mới cần ít nhất 1 chữ số"),
        ("Abcdefg1", "Mật khẩu mới cần ít nhất 1 ký tự đặc biệt"),
        ("Abcdef1 ", "Mật khẩu mới cần ít nhất 1 ký tự đặc biệt"),
        # Chỉ tính chữ hoa/chữ số ASCII, giống regex [A-Z], [0-9] ở frontend
        ("Đàoabcd2!", "Mật khẩu mới cần ít nhất 1 chữ cái viết hoa"),
        ("Abcdefg²!", "Mật khẩu mới cần ít nhất 1 chữ số"),
        ("Abcdefg٣!", "Mật khẩu mới cần ít nhất 1 chữ số"),
        # Khoảng trắng theo đúng \s của JavaScript, không theo str.isspace()
        ("Abcdef1\ufeff", "Mật khẩu mới cần ít nhất 1 ký tự đặc biệt"),
        ("Abcdef1\u3000", "Mật khẩu mới cần ít nhất 1 ký tự đặc biệt"),
    ],
)
def test_weak_new_password_is_rejected(password, message):
    # Validator raise thẳng AppError (handler toàn cục trả 422 WEAK_PASSWORD)
    with pytest.raises(WeakPasswordError) as exc:
        ChangePasswordRequest(
            current_password=PASSWORD, new_password=password, confirm_password=password
        )
    assert exc.value.message == message


# \x1c-\x1f, \x85: str.isspace() coi là khoảng trắng nhưng \s của JavaScript thì không
@pytest.mark.parametrize(
    "password", ["Abcdef1!", "Mk_2026.utc", "Xin-Chao-9", "Abcdef1\x1c", "Abcdef1\x85"]
)
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
        email="NguyenVanB@st.utc2.edu.vn",
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
