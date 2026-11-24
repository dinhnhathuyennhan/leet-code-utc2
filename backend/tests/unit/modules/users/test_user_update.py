"""Test service sửa tài khoản (update_user)."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import Role
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Class, User
from app.modules.users.schemas import UpdateUserRequest, student_email
from app.modules.users.service import (
    FieldNotEditableError,
    NotAllowedToManageAccountError,
    UserNotFoundError,
    update_user,
)
from tests.support.fixtures.builders import make_course, make_enrollment

pytest_plugins = ("tests.support.fixtures.db_fixtures",)

OLD_CODE = "6851071001"


def _user(session, role_id: int, name: str, student_code: str | None = None, **extra) -> User:
    if role_id == Role.STUDENT:
        student_code = student_code or f"{uuid.uuid5(uuid.NAMESPACE_DNS, name).int % 10**10:010d}"
        extra.setdefault("email", student_email(student_code))
    else:
        extra.setdefault("email", f"{name}@example.com")
    user = User(
        user_id=uuid.uuid4(),
        student_code=student_code,
        full_name=name,
        hashed_password="placeholder-hash",
        role_id=role_id,
        **extra,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _class(session, class_id: str) -> Class:
    cls = Class(class_id=class_id, type="CQ", course_number=67, department="CNTT")
    session.add(cls)
    session.commit()
    return cls


@pytest.fixture
def admin(session):
    return _user(session, Role.ADMIN, "admin")


@pytest.fixture
def teacher(session):
    return _user(session, Role.TEACHER, "teacher")


@pytest.fixture
def student(session):
    return _user(session, Role.STUDENT, "student", student_code=OLD_CODE)


@pytest.fixture
def enrolled_student(session, teacher, student):
    make_enrollment(session, make_course(session, teacher, "CS_UPD"), student)
    session.commit()
    return student


# ---------- happy path ----------


def test_admin_updates_teacher_name_and_email(session, admin, teacher):
    result = update_user(
        session,
        admin,
        teacher.user_id,
        UpdateUserRequest(full_name="Cô  Lan", email="lan@st.utc2.edu.vn"),
    )

    assert result.full_name == "Cô Lan"
    assert result.email == "lan@st.utc2.edu.vn"


def test_admin_changes_student_code_rewrites_email(session, admin, student):
    result = update_user(
        session, admin, student.user_id, UpdateUserRequest(student_code="6851071002")
    )

    assert result.student_code == "6851071002"
    assert result.email == "6851071002@st.utc2.edu.vn"


def test_admin_moves_student_to_existing_class(session, admin, student):
    _class(session, "CQ.67.CNTT")

    result = update_user(session, admin, student.user_id, UpdateUserRequest(class_id="CQ.67.CNTT"))

    assert result.class_id == "CQ.67.CNTT"


def test_teacher_updates_enrolled_student(session, teacher, enrolled_student):
    result = update_user(
        session, teacher, enrolled_student.user_id, UpdateUserRequest(full_name="Trần B")
    )

    assert result.full_name == "Trần B"


def test_update_ignores_role_id_and_keeps_password_and_token_version(session, admin, student):
    before = (student.hashed_password, student.token_version, student.must_change_password)
    data = UpdateUserRequest(**{"role_id": 1, "is_active": False, "full_name": "Tên Mới"})

    result = update_user(session, admin, student.user_id, data)

    assert result.full_name == "Tên Mới"
    assert result.role_id == Role.STUDENT
    assert result.is_active is True
    assert (result.hashed_password, result.token_version, result.must_change_password) == before


@pytest.mark.parametrize("payload", [{}, {"full_name": None, "email": None}])
def test_update_empty_or_null_body_is_noop(session, admin, teacher, monkeypatch, payload):
    def fail_commit():
        raise AssertionError("không được commit khi không có thay đổi")

    monkeypatch.setattr(session, "commit", fail_commit)

    result = update_user(session, admin, teacher.user_id, UpdateUserRequest(**payload))

    assert result.full_name == "teacher"


def test_same_student_code_keeps_current_email(session, admin):
    legacy = _user(
        session, Role.STUDENT, "legacy", student_code=OLD_CODE, email="legacy@st.utc2.edu.vn"
    )

    result = update_user(session, admin, legacy.user_id, UpdateUserRequest(student_code=OLD_CODE))

    assert result.email == "legacy@st.utc2.edu.vn"


# ---------- field whitelist ----------


def test_update_student_email_rejected(session, admin, student):
    with pytest.raises(FieldNotEditableError, match="Email sinh viên được tạo tự động"):
        update_user(
            session,
            admin,
            student.user_id,
            UpdateUserRequest(full_name="X", email="new@st.utc2.edu.vn"),
        )
    session.refresh(student)
    assert student.full_name == "student"


@pytest.mark.parametrize("payload", [{"student_code": "6851071009"}, {"class_id": "CQ.67.CNTT"}])
def test_update_teacher_student_code_or_class_rejected(session, admin, teacher, payload):
    _class(session, "CQ.67.CNTT")

    with pytest.raises(FieldNotEditableError, match="Chỉ tài khoản sinh viên"):
        update_user(session, admin, teacher.user_id, UpdateUserRequest(**payload))


# ---------- conflicts ----------


def test_duplicate_teacher_email_conflict_leaves_target_unchanged(session, admin, teacher):
    other = _user(session, Role.TEACHER, "other", email="other@st.utc2.edu.vn")

    with pytest.raises(ConflictError, match="Email đã được đăng ký"):
        update_user(
            session,
            admin,
            teacher.user_id,
            UpdateUserRequest(full_name="Đổi", email=other.email),
        )
    session.refresh(teacher)
    assert teacher.full_name == "teacher"
    assert teacher.email == "teacher@example.com"


def test_teacher_keeping_own_email_is_not_conflict(session, admin):
    teacher = _user(session, Role.TEACHER, "tt", email="t@st.utc2.edu.vn")

    result = update_user(
        session,
        admin,
        teacher.user_id,
        UpdateUserRequest(email="t@st.utc2.edu.vn", full_name="Giữ"),
    )

    assert result.full_name == "Giữ"


def test_duplicate_student_code_conflict(session, admin, student):
    _user(session, Role.STUDENT, "other", student_code="6851071002")

    with pytest.raises(ConflictError, match="Mã sinh viên đã được sử dụng"):
        update_user(
            session,
            admin,
            student.user_id,
            UpdateUserRequest(student_code="6851071002", full_name="Đổi"),
        )
    session.refresh(student)
    assert student.student_code == OLD_CODE
    assert student.full_name == "student"


def test_student_code_whose_derived_email_is_taken_conflict(session, admin, student):
    _user(session, Role.TEACHER, "squatter", email="6851071003@st.utc2.edu.vn")

    with pytest.raises(ConflictError, match=r"6851071003@st\.utc2\.edu\.vn đã được đăng ký"):
        update_user(
            session, admin, student.user_id, UpdateUserRequest(student_code="6851071003")
        )
    session.refresh(student)
    assert student.student_code == OLD_CODE
    assert student.email == student_email(OLD_CODE)


def test_missing_class_not_found_applies_no_other_change(session, admin, student):
    with pytest.raises(NotFoundError, match="Không tìm thấy lớp học có ID: NOPE"):
        update_user(
            session,
            admin,
            student.user_id,
            UpdateUserRequest(full_name="Đổi", class_id="NOPE"),
        )
    session.refresh(student)
    assert student.full_name == "student"
    assert student.class_id is None


def test_integrity_error_on_commit_maps_to_conflict(session, admin, student, monkeypatch):
    def boom():
        raise IntegrityError("stmt", {}, Exception("dup"))

    monkeypatch.setattr(session, "commit", boom)

    with pytest.raises(ConflictError, match="Email hoặc mã sinh viên đã được sử dụng"):
        update_user(session, admin, student.user_id, UpdateUserRequest(full_name="Đổi"))


# ---------- permissions / not found ----------


def test_update_permission_matrix(session, admin, teacher, student):
    other_admin = _user(session, Role.ADMIN, "admin2")
    other_teacher = _user(session, Role.TEACHER, "other")
    foreign_student = _user(session, Role.STUDENT, "foreign")
    make_enrollment(session, make_course(session, other_teacher, "CS_OTHER"), foreign_student)
    session.commit()
    student_caller = _user(session, Role.STUDENT, "caller3")
    unknown_caller = _user(session, 99, "caller99")
    data = UpdateUserRequest(full_name="Hack")

    denied = [
        (admin, other_admin),
        (teacher, foreign_student),  # sinh viên của giáo viên khác
        (teacher, student),  # chưa ghi danh khoá nào của teacher
        (teacher, other_teacher),
        (teacher, admin),
        (teacher, teacher),  # giáo viên không tự sửa tài khoản của mình
        (student_caller, student),
        (student_caller, student_caller),  # sinh viên không tự sửa tài khoản của mình
        (unknown_caller, student),
        (unknown_caller, unknown_caller),
    ]
    for caller, target in denied:
        name = target.full_name
        with pytest.raises(NotAllowedToManageAccountError):
            update_user(session, caller, target.user_id, data)
        session.refresh(target)
        assert target.full_name == name


def test_admin_updates_own_name_and_email(session, admin):
    updated = update_user(
        session,
        admin,
        admin.user_id,
        UpdateUserRequest(full_name="Quản trị viên", email="quantri@st.utc2.edu.vn"),
    )

    assert updated.full_name == "Quản trị viên"
    assert updated.email == "quantri@st.utc2.edu.vn"
    assert updated.role_id == Role.ADMIN
    assert updated.token_version == 0


@pytest.mark.parametrize("payload", [{"student_code": "6851071009"}, {"class_id": "CQ.67.CNTT"}])
def test_admin_self_student_code_or_class_rejected(session, admin, payload):
    with pytest.raises(FieldNotEditableError):
        update_user(session, admin, admin.user_id, UpdateUserRequest(**payload))
    session.refresh(admin)
    assert admin.student_code is None
    assert admin.class_id is None


def test_admin_self_duplicate_email_conflict_leaves_admin_unchanged(session, admin):
    taken = _user(session, Role.TEACHER, "gv2", email="gv2@st.utc2.edu.vn")

    with pytest.raises(ConflictError, match="Email đã được đăng ký"):
        update_user(
            session,
            admin,
            admin.user_id,
            UpdateUserRequest(full_name="Đổi tên", email=taken.email),
        )
    session.refresh(admin)
    assert admin.full_name == "admin"
    assert admin.email == "admin@example.com"


@pytest.mark.parametrize("target_id", [uuid.uuid4(), "not-a-uuid"])
def test_update_unknown_user_not_found(session, admin, target_id):
    with pytest.raises(UserNotFoundError):
        update_user(session, admin, target_id, UpdateUserRequest(full_name="X"))


def test_update_class_vanishing_before_commit_reports_not_found(fk_session, monkeypatch):
    """Lớp bị xoá/đổi tên sau bước kiểm tra tồn tại: lỗi FK phải báo 404 lớp, không phải trùng email/MSSV."""
    admin = _user(fk_session, Role.ADMIN, "admin")
    student = _user(fk_session, Role.STUDENT, "sv", student_code=OLD_CODE)
    student_id = student.user_id
    real_get = fk_session.get
    calls = {"class": 0}

    def get_with_stale_precheck(entity, ident, *args, **kwargs):
        if entity is Class:
            calls["class"] += 1
            if calls["class"] == 1:  # bước kiểm tra tồn tại thấy lớp, rồi lớp biến mất trước commit
                return Class(class_id=ident, type="CQ", course_number=67, department="CNTT")
        return real_get(entity, ident, *args, **kwargs)

    monkeypatch.setattr(fk_session, "get", get_with_stale_precheck)

    with pytest.raises(NotFoundError, match=r"Không tìm thấy lớp học có ID: CQ\.67\.CNTT"):
        update_user(fk_session, admin, student_id, UpdateUserRequest(class_id="CQ.67.CNTT"))

    fk_session.expire_all()
    assert real_get(User, student_id).class_id is None
