"""
Test cho auth_service (login / change_password / refresh_access_token).
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.core import token as token_mod
from app.core.exceptions import AppError, TokenError
from app.core.password import hash_password, verify_password
from app.core.token import create_access_token, create_refresh_token
from app.schemas.auth import ChangePasswordRequest, LoginRequest
from app.services import auth_service as svc
from models import User
from pydantic import ValidationError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

PASSWORD = "Old-Password-123"
NEW_PASSWORD = "New-Password-456"
BAD_PASSWORD = "Wrong-Password-999"  # >= 8 ký tự để qua validate của schema


# ---------------------------------------------------------------- fixtures
@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    # JWT_SECRET_KEY đọc từ env lúc import; trong test luôn ép một secret cố định.
    monkeypatch.setattr(token_mod, "JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _make_user(session: Session, **overrides) -> User:
    fields = {
        "user_id": "U001",
        "full_name": "Nguyen Van A",
        "email": "a@example.com",
        "hashed_password": hash_password(PASSWORD),
        "role_id": 1,
        "must_change_password": False,
        "token_version": 0,
    }
    fields.update(overrides)
    user = User(**fields)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def user(session):
    return _make_user(session)


def _forge(payload: dict) -> str:
    """Ký token bằng đúng secret của app, để test các payload mà create_* không tạo ra."""
    return jwt.encode(payload, token_mod.JWT_SECRET_KEY, algorithm=token_mod.JWT_ALGORITHM)


def _login_req(email="a@example.com", password=PASSWORD) -> LoginRequest:
    return LoginRequest(email=email, password=password)


def _change_req(current=PASSWORD, new=NEW_PASSWORD, confirm=None) -> ChangePasswordRequest:
    return ChangePasswordRequest(
        current_password=current,
        new_password=new,
        confirm_password=new if confirm is None else confirm,
    )


def _assert_app_error(exc_info, status: int, code: str | None = None):
    assert exc_info.value.status_code == status
    if code:
        assert exc_info.value.error_code == code


# ------------------------------------------------------------------- login
class TestLogin:
    def test_success_returns_tokens_and_user_info(self, session, user):
        response, refresh_token = svc.login(session, _login_req())

        assert response.access_token
        assert refresh_token
        assert response.user.user_id == user.user_id
        assert response.user.email == user.email
        assert response.user.role_id == user.role_id

    def test_response_does_not_leak_password_hash(self, session, user):
        response, _ = svc.login(session, _login_req())
        assert "hashed_password" not in response.model_dump_json()
        assert user.hashed_password not in response.model_dump_json()

    def test_refresh_token_carries_current_token_version(self, session):
        from app.core.token import decode_token

        _make_user(session, token_version=7)
        _, refresh_token = svc.login(session, _login_req())
        assert decode_token(refresh_token, "refresh")["tv"] == 7

    def test_reports_must_change_password_flag(self, session):
        _make_user(session, must_change_password=True)
        response, _ = svc.login(session, _login_req())
        assert response.user.must_change_password is True

    def test_wrong_password_rejected(self, session, user):
        with pytest.raises(svc.InvalidCredentialsError) as exc:
            svc.login(session, _login_req(password=BAD_PASSWORD))
        _assert_app_error(exc, 401, "INVALID_CREDENTIALS")

    def test_unknown_email_rejected_with_same_error_as_wrong_password(
            self, session, user
    ):
        with pytest.raises(svc.InvalidCredentialsError) as unknown:
            svc.login(session, _login_req(email="nobody@example.com"))
        with pytest.raises(svc.InvalidCredentialsError) as wrong_pw:
            svc.login(session, _login_req(password=BAD_PASSWORD))

        # Không cho phép phân biệt "email không tồn tại" và "sai mật khẩu"
        assert str(unknown.value) == str(wrong_pw.value)
        assert unknown.value.status_code == wrong_pw.value.status_code
        assert unknown.value.error_code == wrong_pw.value.error_code

    def test_unknown_email_still_runs_password_hash_check(
            self, session, user, monkeypatch
    ):
        """Regression: timing attack / user enumeration.

        Email không tồn tại từng bỏ qua verify_password nên response nhanh hơn -> kẻ tấn công
        dò được email nào có tài khoản. Nay luôn verify với hash giả.
        """
        calls = []
        real = svc.verify_password

        def spy(**kwargs):
            calls.append(kwargs)
            return real(**kwargs)

        monkeypatch.setattr(svc, "verify_password", spy)

        with pytest.raises(svc.InvalidCredentialsError):
            svc.login(session, _login_req(email="nobody@example.com"))

        assert len(calls) == 1

    @pytest.mark.parametrize("typed", ["A@Example.COM", "a@EXAMPLE.com", "A@EXAMPLE.COM"])
    def test_email_lookup_is_case_insensitive(self, session, user, typed):
        """Email không phân biệt hoa/thường khi đăng nhập (bàn phím điện thoại hay tự viết hoa)."""
        response, _ = svc.login(session, _login_req(email=typed))
        assert response.user.user_id == user.user_id

    def test_case_insensitive_login_still_checks_password(self, session, user):
        with pytest.raises(svc.InvalidCredentialsError):
            svc.login(session, _login_req(email="A@EXAMPLE.COM", password=BAD_PASSWORD))

    def test_empty_stored_hash_is_rejected_not_500(self, session):
        """Regression: Tài khoản chưa có mật khẩu hợp lệ không được làm crash login."""
        _make_user(session, email="nopass@example.com", hashed_password="")
        with pytest.raises(svc.InvalidCredentialsError):
            svc.login(session, _login_req(email="nopass@example.com"))


# ---------------------------------------------------------- change_password
class TestChangePassword:
    def test_success_updates_hash_flag_and_token_version(self, session):
        user = _make_user(session, must_change_password=True, token_version=3)

        response, refresh_token = svc.change_password(session, user, _change_req())

        session.refresh(user)
        assert verify_password(password=NEW_PASSWORD, hashed_password=user.hashed_password)
        assert not verify_password(password=PASSWORD, hashed_password=user.hashed_password)
        assert user.must_change_password is False
        assert user.token_version == 4
        assert response.access_token
        assert refresh_token
        assert response.user.must_change_password is False

    def test_new_password_is_stored_hashed(self, session, user):
        svc.change_password(session, user, _change_req())
        session.refresh(user)
        assert user.hashed_password != NEW_PASSWORD

    def test_wrong_current_password_rejected_and_nothing_changes(self, session, user):
        old_hash, old_version = user.hashed_password, user.token_version

        with pytest.raises(svc.WrongCurrentPasswordError) as exc:
            svc.change_password(session, user, _change_req(current=BAD_PASSWORD))

        _assert_app_error(exc, 401, "WRONG_PASSWORD")
        session.refresh(user)
        assert user.hashed_password == old_hash
        assert user.token_version == old_version

    def test_same_password_rejected_and_nothing_changes(self, session, user):
        old_hash, old_version = user.hashed_password, user.token_version

        with pytest.raises(svc.SamePasswordError) as exc:
            svc.change_password(session, user, _change_req(new=PASSWORD))

        _assert_app_error(exc, 400, "SAME_PASSWORD")
        session.refresh(user)
        assert user.hashed_password == old_hash
        assert user.token_version == old_version

    def test_wrong_current_password_checked_before_same_password(self, session, user):
        """Sai mật khẩu hiện tại phải ưu tiên, tránh lộ thông tin qua lỗi SAME_PASSWORD."""
        with pytest.raises(svc.WrongCurrentPasswordError):
            svc.change_password(session, user, _change_req(current=BAD_PASSWORD, new=BAD_PASSWORD))

    def test_mismatched_confirm_password_is_rejected(self, session, user):
        """confirm_password khác new_password phải bị chặn và DB không đổi.

        Service không tự so sánh hai field này, nên việc chặn phải nằm ở schema
        (model_validator) - hoặc ở service nếu bạn chọn kiểm ở đó. Test chấp nhận cả hai.
        """
        old_hash, old_version = user.hashed_password, user.token_version

        try:
            request = _change_req(confirm="Different-Password-000")
        except (ValidationError, AppError):
            return  # schema đã chặn: đúng

        with pytest.raises(AppError):
            svc.change_password(session, user, request)

        session.refresh(user)
        assert user.hashed_password == old_hash
        assert user.token_version == old_version

    def test_old_refresh_token_revoked_after_change(self, session, user):
        _, old_refresh = svc.login(session, _login_req())

        svc.change_password(session, user, _change_req())

        with pytest.raises(svc.SessionRevokedError):
            svc.refresh_access_token(session, old_refresh)

    def test_new_refresh_token_works_after_change(self, session, user):
        _, new_refresh = svc.change_password(session, user, _change_req())
        assert svc.refresh_access_token(session, new_refresh)

    def test_old_password_no_longer_logs_in(self, session, user):
        svc.change_password(session, user, _change_req())
        with pytest.raises(svc.InvalidCredentialsError):
            svc.login(session, _login_req(password=PASSWORD))
        response, _ = svc.login(session, _login_req(password=NEW_PASSWORD))
        assert response.access_token

    def test_concurrent_changes_do_not_lose_token_version_increment(self, engine):
        """Regression: race condition. `user.token_version += 1` là read-modify-write nên hai
        request cùng đọc 0 rồi cùng ghi 1 -> mất một lần tăng. Nay dùng UPDATE nguyên tử.
        """
        with Session(engine) as s:
            _make_user(s)

        with Session(engine) as s1, Session(engine) as s2:
            u1 = s1.get(User, "U001")
            u2 = s2.get(User, "U001")  # cả hai cùng thấy token_version = 0

            svc.change_password(s1, u1, _change_req(PASSWORD, "Aaaa-1111-bbbb"))
            svc.change_password(s2, u2, _change_req(PASSWORD, "Cccc-2222-dddd"))

        with Session(engine) as s:
            assert s.get(User, "U001").token_version == 2


# ---------------------------------------------------- refresh_access_token
class TestRefreshAccessToken:
    @pytest.mark.parametrize("token", [None, ""])
    def test_missing_token_means_session_expired(self, session, token):
        with pytest.raises(svc.SessionExpiredError) as exc:
            svc.refresh_access_token(session, token)
        _assert_app_error(exc, 401, "SESSION_EXPIRED")

    def test_valid_token_returns_new_access_token(self, session, user):
        refresh = create_refresh_token(user_id=user.user_id, token_version=user.token_version)
        access = svc.refresh_access_token(session, refresh)
        assert isinstance(access, str)
        assert access

    def test_token_version_mismatch_is_revoked(self, session, user):
        refresh = create_refresh_token(user_id=user.user_id, token_version=user.token_version)
        user.token_version += 1
        session.add(user)
        session.commit()

        with pytest.raises(svc.SessionRevokedError) as exc:
            svc.refresh_access_token(session, refresh)
        _assert_app_error(exc, 401, "SESSION_REVOKED")

    def test_deleted_user_is_revoked(self, session, user):
        refresh = create_refresh_token(user_id=user.user_id, token_version=user.token_version)
        session.delete(user)
        session.commit()

        with pytest.raises(svc.SessionRevokedError):
            svc.refresh_access_token(session, refresh)

    def test_garbage_token_returns_401_not_500(self, session):
        """Regression: token rác / hết hạn từng làm lộ exception của thư viện JWT -> HTTP 500."""
        with pytest.raises(AppError) as exc:
            svc.refresh_access_token(session, "not-a-jwt")
        assert exc.value.status_code == 401

    def test_expired_token_returns_session_expired(self, session, user):
        """Regression: token hết hạn từng lọt ExpiredSignatureError ra ngoài -> 500."""
        expired = _forge(
            {"sub": user.user_id, "tv": 0, "type": "refresh",
             "exp": datetime.now(UTC) - timedelta(hours=1)}
        )
        with pytest.raises(svc.SessionExpiredError):
            svc.refresh_access_token(session, expired)

    def test_token_signed_with_wrong_secret_rejected(self, session, user):
        """Regression: token sai chữ ký từng lọt InvalidSignatureError ra ngoài -> 500."""
        forged = jwt.encode(
            {"sub": user.user_id, "tv": 0, "type": "refresh",
             "exp": datetime.now(UTC) + timedelta(days=1)},
            "another-secret-another-secret-123456",
            algorithm="HS256",
        )
        with pytest.raises(AppError) as exc:
            svc.refresh_access_token(session, forged)
        assert exc.value.status_code == 401

    def test_alg_none_token_rejected(self, session, user):
        """Regression: alg=none luôn bị từ chối (decode_token pin HS256), và phải ra 401 chứ không 500."""
        unsigned = jwt.encode(
            {"sub": user.user_id, "tv": 0, "type": "refresh",
             "exp": datetime.now(UTC) + timedelta(days=1)},
            None,
            algorithm="none",
        )
        with pytest.raises(AppError) as exc:
            svc.refresh_access_token(session, unsigned)
        assert exc.value.status_code == 401

    def test_token_without_exp_is_rejected(self, session, user):
        """Regression: token không có exp từng sống vĩnh viễn (jwt.decode chỉ kiểm exp nếu có claim)."""
        no_exp = _forge({"sub": user.user_id, "tv": 0, "type": "refresh"})
        with pytest.raises(AppError) as exc:
            svc.refresh_access_token(session, no_exp)
        assert exc.value.status_code == 401

    def test_token_error_is_mapped_to_session_expired(self, session, monkeypatch):
        """TokenError (từ decode_token) phải được đổi thành SESSION_EXPIRED để client biết
        cần đăng nhập lại (thay vì INVALID_TOKEN chung chung).
        Việc token thiếu claim / sai loại được test ở test_token.py."""

        def boom(_token, _expected_type):
            raise TokenError("Token không hợp lệ")

        monkeypatch.setattr(svc, "decode_token", boom)

        with pytest.raises(svc.SessionExpiredError) as exc:
            svc.refresh_access_token(session, "any")
        _assert_app_error(exc, 401, "SESSION_EXPIRED")

    def test_refresh_requires_refresh_type_token(self, session, user, monkeypatch):
        """Regression: service phải yêu cầu đúng loại token "refresh" từ decode_token."""
        seen = {}

        def spy(token, expected_type):
            seen["expected_type"] = expected_type
            return {"sub": user.user_id, "tv": user.token_version, "type": expected_type}

        monkeypatch.setattr(svc, "decode_token", spy)

        assert svc.refresh_access_token(session, "any")
        assert seen["expected_type"] == "refresh"

    def test_access_token_cannot_be_used_as_refresh_token(self, session, user):
        """Regression: access token có sẵn sub + tv nên từng được chấp nhận như refresh token:
        token 15 phút bị lộ có thể tự gia hạn đến khi đổi mật khẩu."""
        access = create_access_token(
            user_id=user.user_id, role_id=user.role_id, token_version=user.token_version
        )
        with pytest.raises(AppError) as exc:
            svc.refresh_access_token(session, access)
        assert exc.value.status_code == 401

    def test_string_sub_claim_is_resolved_to_user(self, session, user, monkeypatch):
        """Regression: sub luôn là str (PyJWT >= 2.10 bắt buộc) và khớp PK str của User."""
        monkeypatch.setattr(
            svc,
            "decode_token",
            lambda _t, _type: {"sub": str(user.user_id), "tv": user.token_version, "type": "refresh"},
        )
        assert svc.refresh_access_token(session, "any")

    def test_new_access_token_uses_current_role(self, session, user, monkeypatch):
        refresh = create_refresh_token(user_id=user.user_id, token_version=user.token_version)
        user.role_id = 2  # đổi quyền sau khi cấp refresh token
        session.add(user)
        session.commit()

        captured = {}

        def fake_create_access_token(user_id, role_id, token_version):
            captured.update(user_id=user_id, role_id=role_id, token_version=token_version)
            return "fake-access"

        monkeypatch.setattr(svc, "create_access_token", fake_create_access_token)

        assert svc.refresh_access_token(session, refresh) == "fake-access"
        assert captured["role_id"] == 2
