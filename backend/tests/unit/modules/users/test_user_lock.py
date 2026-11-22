"""Test service khoá / mở khoá tài khoản (lock_user / unlock_user)."""

import uuid

import pytest
from sqlmodel import update

from app.core.dependencies import Role
from app.core.exceptions import AccountLockedError, ConflictError
from app.core.security import tokens as token_mod
from app.core.security.passwords import hash_password
from app.core.security.tokens import create_refresh_token
from app.models import User
from app.modules.auth import service as auth_svc
from app.modules.auth.schemas import LoginRequest
from app.modules.users import service as user_svc
from app.modules.users.service import (
    UNLOCK_FORBIDDEN,
    NotAllowedToManageAccountError,
    UserNotFoundError,
    lock_user,
    unlock_user,
)
from tests.support.fixtures.builders import make_course, make_enrollment

PASSWORD = "Old-Password-123"


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setattr(token_mod, "JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")


def _user(session, role_id: int, name: str, **overrides) -> User:
    student_code = None
    if role_id == Role.STUDENT:
        student_code = f"{uuid.uuid5(uuid.NAMESPACE_DNS, name).int % 10**10:010d}"
    user = User(
        user_id=uuid.uuid4(),
        student_code=student_code,
        full_name=name,
        email=f"{name}@example.com",
        hashed_password=hash_password(PASSWORD),
        role_id=role_id,
        **overrides,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def admin(session):
    return _user(session, Role.ADMIN, "admin")


@pytest.fixture
def teacher(session):
    return _user(session, Role.TEACHER, "teacher")


@pytest.fixture
def student(session):
    return _user(session, Role.STUDENT, "student")


@pytest.fixture
def enrolled_student(session, teacher, student):
    course = make_course(session, teacher, "CS_LOCK")
    make_enrollment(session, course, student)
    session.commit()
    return student


# ---------- happy path ----------


def test_admin_locks_teacher_and_bumps_token_version_once(session, admin, teacher):
    result = lock_user(session, admin, teacher.user_id)

    assert result.is_active is False
    assert result.token_version == 1


def test_admin_locks_student(session, admin, student):
    assert lock_user(session, admin, student.user_id).is_active is False


def test_teacher_locks_enrolled_student(session, teacher, enrolled_student):
    result = lock_user(session, teacher, str(enrolled_student.user_id))

    assert result.is_active is False
    assert result.token_version == 1


# ---------- idempotency ----------


def test_lock_already_locked_is_noop_without_second_bump(session, admin, student):
    lock_user(session, admin, student.user_id)

    result = lock_user(session, admin, student.user_id)

    assert result.is_active is False
    assert result.token_version == 1


def test_unlock_restores_login_without_bumping_token_version(session, admin, student):
    lock_user(session, admin, student.user_id)

    result = unlock_user(session, admin, student.user_id)

    assert result.is_active is True
    assert result.token_version == 1
    response, _ = auth_svc.login(
        session, LoginRequest(email=student.email, password=PASSWORD)
    )
    assert response.access_token


def test_unlock_active_account_is_noop(session, admin, student):
    result = unlock_user(session, admin, student.user_id)

    assert result.is_active is True
    assert result.token_version == 0


# ---------- permissions ----------


def test_teacher_cannot_lock_student_outside_own_courses(session, teacher, student):
    with pytest.raises(NotAllowedToManageAccountError):
        lock_user(session, teacher, student.user_id)
    session.refresh(student)
    assert student.is_active is True
    assert student.token_version == 0


def test_teacher_cannot_lock_student_of_other_teacher(session, teacher, student):
    other = _user(session, Role.TEACHER, "other")
    make_enrollment(session, make_course(session, other, "CS_OTHER"), student)
    session.commit()

    with pytest.raises(NotAllowedToManageAccountError):
        lock_user(session, teacher, student.user_id)


def test_teacher_cannot_lock_teacher_admin_or_self(session, admin, teacher):
    other_teacher = _user(session, Role.TEACHER, "other")
    for target in (other_teacher, admin, teacher):
        with pytest.raises(NotAllowedToManageAccountError):
            lock_user(session, teacher, target.user_id)
        session.refresh(target)
        assert target.is_active is True
        assert target.token_version == 0


def test_admin_cannot_lock_admin_or_self(session, admin):
    other_admin = _user(session, Role.ADMIN, "admin2")
    for target in (other_admin, admin):
        with pytest.raises(NotAllowedToManageAccountError):
            lock_user(session, admin, target.user_id)
        session.refresh(target)
        assert target.is_active is True
        assert target.token_version == 0


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_cannot_lock(session, student, role_id):
    caller = _user(session, role_id, f"caller{role_id}")
    with pytest.raises(NotAllowedToManageAccountError):
        lock_user(session, caller, student.user_id)
    with pytest.raises(NotAllowedToManageAccountError):
        unlock_user(session, caller, student.user_id)
    session.refresh(student)
    assert student.is_active is True
    assert student.token_version == 0


def test_unlock_by_unauthorized_caller_leaves_locked_target_unchanged(session, admin, teacher, student):
    lock_user(session, admin, student.user_id)

    with pytest.raises(NotAllowedToManageAccountError):
        unlock_user(session, teacher, student.user_id)

    session.refresh(student)
    assert student.is_active is False


# ---------- locked_by: ai khoá thì ai được mở ----------


def test_lock_records_locker_and_unlock_clears_it(session, teacher, enrolled_student):
    assert lock_user(session, teacher, enrolled_student.user_id).locked_by == teacher.user_id

    assert unlock_user(session, teacher, enrolled_student.user_id).locked_by is None


def test_teacher_cannot_unlock_account_locked_by_admin(
    session, admin, teacher, enrolled_student
):
    lock_user(session, admin, enrolled_student.user_id)

    with pytest.raises(NotAllowedToManageAccountError) as exc:
        unlock_user(session, teacher, enrolled_student.user_id)

    assert exc.value.message == UNLOCK_FORBIDDEN
    session.refresh(enrolled_student)
    assert enrolled_student.is_active is False
    assert enrolled_student.locked_by == admin.user_id


def test_admin_can_unlock_account_locked_by_teacher(session, admin, teacher, enrolled_student):
    lock_user(session, teacher, enrolled_student.user_id)

    result = unlock_user(session, admin, enrolled_student.user_id)

    assert result.is_active is True
    assert result.locked_by is None


def test_teacher_can_unlock_account_locked_by_another_teacher_of_student(
    session, teacher, enrolled_student
):
    other = _user(session, Role.TEACHER, "other")
    make_enrollment(session, make_course(session, other, "CS_OTHER"), enrolled_student)
    session.commit()
    lock_user(session, other, enrolled_student.user_id)

    assert unlock_user(session, teacher, enrolled_student.user_id).is_active is True


def test_teacher_relock_does_not_take_over_admin_lock(session, admin, teacher, enrolled_student):
    lock_user(session, admin, enrolled_student.user_id)

    result = lock_user(session, teacher, enrolled_student.user_id)

    assert result.locked_by == admin.user_id
    assert result.token_version == 1
    with pytest.raises(NotAllowedToManageAccountError):
        unlock_user(session, teacher, enrolled_student.user_id)


def test_admin_relock_takes_over_teacher_lock_without_second_bump(
    session, admin, teacher, enrolled_student
):
    lock_user(session, teacher, enrolled_student.user_id)

    result = lock_user(session, admin, enrolled_student.user_id)

    assert result.is_active is False
    assert result.locked_by == admin.user_id
    assert result.token_version == 1
    with pytest.raises(NotAllowedToManageAccountError):
        unlock_user(session, teacher, enrolled_student.user_id)


@pytest.mark.parametrize("locker", ["missing", "unknown_role", "none"])
def test_teacher_cannot_unlock_when_locker_is_not_a_known_teacher(
    session, teacher, enrolled_student, locker
):
    """Whitelist: người khoá không xác định được là Giáo viên thì chỉ Admin mở khoá."""
    locked_by = {
        "missing": uuid.uuid4(),
        "unknown_role": _user(session, 99, "strange").user_id,
        "none": None,
    }[locker]
    enrolled_student.is_active = False
    enrolled_student.locked_by = locked_by
    session.add(enrolled_student)
    session.commit()

    with pytest.raises(NotAllowedToManageAccountError):
        unlock_user(session, teacher, enrolled_student.user_id)
    session.refresh(enrolled_student)
    assert enrolled_student.is_active is False


def test_teacher_unlock_active_account_is_noop(session, teacher, enrolled_student):
    result = unlock_user(session, teacher, enrolled_student.user_id)

    assert result.is_active is True
    assert result.locked_by is None


# ---------- khoá/mở khoá đồng thời ----------


def _concurrently(session, user, **values):
    """Giả lập request khác đã commit thay đổi lên ``user``."""
    session.exec(update(User).where(User.user_id == user.user_id).values(**values))
    session.commit()


def _inject_before_update(monkeypatch, call_no, action):
    """Chạy ``action`` ngay trước lần UPDATE thứ ``call_no`` của service."""
    original = user_svc._apply_status_update
    calls = {"n": 0}

    def wrapper(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == call_no:
            action()
        return original(*args, **kwargs)

    monkeypatch.setattr(user_svc, "_apply_status_update", wrapper)


def test_admin_lock_racing_teacher_lock_still_ends_locked_by_admin(
    session, monkeypatch, admin, teacher, enrolled_student
):
    _inject_before_update(
        monkeypatch,
        1,
        lambda: _concurrently(
            session,
            enrolled_student,
            is_active=False,
            locked_by=teacher.user_id,
            token_version=User.token_version + 1,
        ),
    )

    result = lock_user(session, admin, enrolled_student.user_id)

    assert result.is_active is False
    assert result.locked_by == admin.user_id
    assert result.token_version == 1  # chỉ lượt khoá của GV tăng version
    monkeypatch.undo()
    with pytest.raises(NotAllowedToManageAccountError):
        unlock_user(session, teacher, enrolled_student.user_id)


def test_admin_lock_racing_teacher_unlock_relocks_account(
    session, monkeypatch, admin, teacher, enrolled_student
):
    lock_user(session, teacher, enrolled_student.user_id)
    _inject_before_update(
        monkeypatch,
        2,
        lambda: _concurrently(session, enrolled_student, is_active=True, locked_by=None),
    )

    result = lock_user(session, admin, enrolled_student.user_id)

    assert result.is_active is False
    assert result.locked_by == admin.user_id
    assert result.token_version == 2


def test_teacher_unlock_racing_admin_relock_is_rejected(
    session, monkeypatch, admin, teacher, enrolled_student
):
    lock_user(session, teacher, enrolled_student.user_id)
    _inject_before_update(
        monkeypatch,
        1,
        lambda: _concurrently(session, enrolled_student, locked_by=admin.user_id),
    )

    with pytest.raises(NotAllowedToManageAccountError) as exc:
        unlock_user(session, teacher, enrolled_student.user_id)

    assert exc.value.message == UNLOCK_FORBIDDEN
    session.refresh(enrolled_student)
    assert enrolled_student.is_active is False
    assert enrolled_student.locked_by == admin.user_id


def test_lock_gives_up_with_conflict_when_status_keeps_flipping(
    session, monkeypatch, admin, student
):
    monkeypatch.setattr(user_svc, "_apply_status_update", lambda *a, **k: 0)

    with pytest.raises(ConflictError):
        lock_user(session, admin, student.user_id)


def test_admin_relock_of_legacy_lock_records_admin_without_bump(session, admin, student):
    _concurrently(session, student, is_active=False, locked_by=None)

    result = lock_user(session, admin, student.user_id)

    assert result.locked_by == admin.user_id
    assert result.token_version == 0


def test_teacher_relock_keeps_other_teacher_as_locker(session, teacher, enrolled_student):
    other = _user(session, Role.TEACHER, "other")
    make_enrollment(session, make_course(session, other, "CS_OTHER"), enrolled_student)
    session.commit()
    lock_user(session, other, enrolled_student.user_id)

    result = lock_user(session, teacher, enrolled_student.user_id)

    assert result.locked_by == other.user_id
    assert result.token_version == 1


# ---------- not found ----------


@pytest.mark.parametrize("target_id", [uuid.uuid4(), "not-a-uuid", ""])
def test_lock_unknown_or_non_uuid_user_raises_not_found(session, admin, target_id):
    with pytest.raises(UserNotFoundError):
        lock_user(session, admin, target_id)
    with pytest.raises(UserNotFoundError):
        unlock_user(session, admin, target_id)


# ---------- effect on auth ----------


def test_locked_user_cannot_login(session, admin, student):
    lock_user(session, admin, student.user_id)

    with pytest.raises(AccountLockedError):
        auth_svc.login(session, LoginRequest(email=student.email, password=PASSWORD))


def test_lock_rejects_existing_refresh_token_as_locked(session, admin, student):
    refresh = create_refresh_token(user_id=student.user_id, token_version=student.token_version)
    assert auth_svc.refresh_access_token(session, refresh)

    lock_user(session, admin, student.user_id)

    with pytest.raises(AccountLockedError):
        auth_svc.refresh_access_token(session, refresh)


def test_old_refresh_token_stays_revoked_after_unlock(session, admin, student):
    refresh = create_refresh_token(user_id=student.user_id, token_version=student.token_version)
    lock_user(session, admin, student.user_id)

    unlock_user(session, admin, student.user_id)

    with pytest.raises(auth_svc.SessionRevokedError):
        auth_svc.refresh_access_token(session, refresh)
