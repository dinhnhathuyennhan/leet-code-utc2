"""Test ``classroom_service``: tạo / xem / xoá lớp hành chính.

SQLite mặc định **không** kiểm tra khoá ngoại, nên các test cần DB chặn
xoá lớp còn sinh viên dùng fixture ``fk_session`` (bật ``PRAGMA foreign_keys``),
giống Postgres thật.
"""

import re

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.core.exceptions import ConflictError, NotFoundError
from app.dependencies import Role
from app.schemas.classroom import ClassResponse, CreateClassRequest
from app.services import classroom_service
from app.services.classroom_service import (
    create_class,
    delete_class,
    get_class,
    list_classes,
)
from models import Class, User


@pytest.fixture()
def fk_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _request(class_type="CQ", course_number=67, department="CNTT") -> CreateClassRequest:
    return CreateClassRequest(
        type=class_type, course_number=course_number, department=department
    )


def _add_class(session, class_type="CQ", course_number=67, department="CNTT") -> Class:
    db_class = Class(
        class_id=f"{class_type}.{course_number}.{department}",
        type=class_type,
        course_number=course_number,
        department=department,
    )
    session.add(db_class)
    session.commit()
    return db_class


def _add_user(session, user_id: str, class_id: str | None, role_id: int = Role.STUDENT) -> User:
    user = User(
        user_id=user_id,
        full_name=f"Người dùng {user_id}",
        email=f"{user_id}@example.com",
        hashed_password="placeholder",
        role_id=role_id,
        class_id=class_id,
    )
    session.add(user)
    session.commit()
    return user


# ---------- create_class ----------


def test_create_class_success(session):
    result = create_class(session, _request("CQ", 67, "KTXDCTGT.2"))

    assert result == ClassResponse(
        class_id="CQ.67.KTXDCTGT.2",
        type="CQ",
        course_number=67,
        department="KTXDCTGT.2",
        student_count=0,
    )
    saved = session.get(Class, "CQ.67.KTXDCTGT.2")
    assert (saved.type, saved.course_number, saved.department) == ("CQ", 67, "KTXDCTGT.2")


def test_create_class_duplicate_raises_conflict(session):
    _add_class(session)

    with pytest.raises(ConflictError, match=re.escape("Lớp CQ.67.CNTT đã tồn tại")):
        create_class(session, _request())

    assert len(session.exec(select(Class)).all()) == 1


def test_create_class_with_different_case_is_another_class(session):
    _add_class(session)

    result = create_class(session, _request("cq"))

    assert result.class_id == "cq.67.CNTT"
    assert len(session.exec(select(Class)).all()) == 2


def test_create_class_race_on_commit_raises_conflict(session, monkeypatch):
    """2 request cùng tạo 1 lớp: cả hai qua bước kiểm tra, request sau vấp khoá chính."""
    _add_class(session)
    session.expunge_all()
    # Mô phỏng request này kiểm tra trước khi request kia kịp lưu lớp
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: None)

    with pytest.raises(ConflictError, match=re.escape("Lớp CQ.67.CNTT đã tồn tại")):
        create_class(session, _request())

    monkeypatch.undo()
    # rollback xong session vẫn dùng tiếp được, lớp có sẵn vẫn còn đúng 1 bản
    assert [c.class_id for c in list_classes(session)] == ["CQ.67.CNTT"]


# ---------- list_classes ----------


def test_list_classes_empty(session):
    assert list_classes(session) == []


def test_list_classes_sorted_with_student_count(session):
    _add_class(session, "CQ", 67, "CNTT")
    _add_class(session, "CQ", 66, "KTXDCTGT.2")
    _add_class(session, "CQ", 68, "CNTT")
    _add_user(session, "sv1", "CQ.67.CNTT")
    _add_user(session, "sv2", "CQ.67.CNTT")
    _add_user(session, "sv3", "CQ.66.KTXDCTGT.2")

    result = list_classes(session)

    assert [(c.class_id, c.student_count) for c in result] == [
        ("CQ.66.KTXDCTGT.2", 1),
        ("CQ.67.CNTT", 2),
        ("CQ.68.CNTT", 0),  # lớp chưa có sinh viên vẫn hiện
    ]


def test_list_classes_does_not_count_users_without_class(session):
    _add_class(session)
    _add_user(session, "sv1", "CQ.67.CNTT")
    _add_user(session, "gv1", None, role_id=Role.TEACHER)
    _add_user(session, "admin1", None, role_id=Role.ADMIN)

    assert [c.student_count for c in list_classes(session)] == [1]


# ---------- get_class ----------


def test_get_class_returns_class_with_student_count(session):
    _add_class(session)
    _add_class(session, "CQ", 68, "CNTT")
    _add_user(session, "sv1", "CQ.67.CNTT")

    result = get_class(session, "CQ.67.CNTT")

    assert result == ClassResponse(
        class_id="CQ.67.CNTT",
        type="CQ",
        course_number=67,
        department="CNTT",
        student_count=1,
    )


def test_get_class_without_students_has_zero_count(session):
    _add_class(session)

    assert get_class(session, "CQ.67.CNTT").student_count == 0


@pytest.mark.parametrize("class_id", ["CQ.99.CNTT", "cq.67.cntt", ""])
def test_get_class_not_found(session, class_id):
    _add_class(session)

    with pytest.raises(NotFoundError, match="Không tìm thấy lớp"):
        get_class(session, class_id)


# ---------- delete_class ----------


def test_delete_class_success(fk_session):
    _add_class(fk_session)
    _add_class(fk_session, "CQ", 68, "CNTT")

    delete_class(fk_session, "CQ.67.CNTT")

    assert fk_session.get(Class, "CQ.67.CNTT") is None
    assert fk_session.get(Class, "CQ.68.CNTT") is not None


def test_delete_class_not_found(fk_session):
    with pytest.raises(NotFoundError, match=re.escape("Không tìm thấy lớp CQ.67.CNTT")):
        delete_class(fk_session, "CQ.67.CNTT")


def test_delete_class_with_students_raises_conflict(fk_session):
    _add_class(fk_session)
    _add_user(fk_session, "sv1", "CQ.67.CNTT")
    _add_user(fk_session, "sv2", "CQ.67.CNTT")

    with pytest.raises(
        ConflictError, match=re.escape("Lớp CQ.67.CNTT đang có 2 sinh viên, không thể xóa")
    ):
        delete_class(fk_session, "CQ.67.CNTT")

    assert fk_session.get(Class, "CQ.67.CNTT") is not None
    assert fk_session.get(User, "sv1").class_id == "CQ.67.CNTT"


def test_delete_class_student_added_after_count_raises_conflict(fk_session, monkeypatch):
    """E2: có sinh viên vào lớp ngay sau bước đếm → khoá ngoại chặn, không xoá.

    Nếu service dùng ``session.delete()``, ORM sẽ tự gán ``class_id = NULL``
    cho sinh viên rồi xoá lớp thành công, và test này sẽ fail.
    """
    _add_class(fk_session)
    real_delete = classroom_service.delete

    def delete_after_student_joins(*args, **kwargs):
        # Mô phỏng request khác vừa gán sinh viên vào lớp, sau bước đếm, trước câu DELETE
        fk_session.add(
            User(
                user_id="sv1",
                full_name="Sinh viên mới",
                email="sv1@example.com",
                hashed_password="placeholder",
                role_id=Role.STUDENT,
                class_id="CQ.67.CNTT",
            )
        )
        fk_session.flush()
        return real_delete(*args, **kwargs)

    monkeypatch.setattr(classroom_service, "delete", delete_after_student_joins)

    with pytest.raises(ConflictError, match=re.escape("Lớp CQ.67.CNTT đang có sinh viên, không thể xóa")):
        delete_class(fk_session, "CQ.67.CNTT")

    # rollback xong session vẫn dùng tiếp được, lớp vẫn còn
    assert fk_session.get(Class, "CQ.67.CNTT") is not None


def test_delete_class_never_touches_students_of_other_classes(fk_session):
    _add_class(fk_session)
    _add_class(fk_session, "CQ", 68, "CNTT")
    _add_user(fk_session, "sv1", "CQ.68.CNTT")

    delete_class(fk_session, "CQ.67.CNTT")

    assert fk_session.get(User, "sv1").class_id == "CQ.68.CNTT"
    assert [c.class_id for c in list_classes(fk_session)] == ["CQ.68.CNTT"]
