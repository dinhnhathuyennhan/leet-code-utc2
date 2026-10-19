import pytest
from sqlmodel import Session

from app.models import Course, User
from tests.support.fixtures.user_fixtures import vn


@pytest.fixture
def course(session: Session, owner_teacher: User) -> Course:
    course = Course(
        course_id="CS101",
        course_name="Nhập môn lập trình",
        created_by=owner_teacher.user_id,
        term="HK1 2026-2027",
        start_date=vn(2026, 9, 7),
        end_date=vn(2026, 12, 27),
        total_number_student=0,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def make_course(session: Session, course_id: str, owner: User) -> Course:
    """Create an additional course for tests that need multiple courses."""
    course = Course(
        course_id=course_id,
        course_name=f"Lớp {course_id}",
        created_by=owner.user_id,
        term="HK1 2026-2027",
        start_date=vn(2026, 9, 7),
        end_date=vn(2026, 12, 27),
        total_number_student=0,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course
