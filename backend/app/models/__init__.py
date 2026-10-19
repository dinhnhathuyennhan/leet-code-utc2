"""Tập hợp mọi model SQLModel.

Import package này là đủ để ``SQLModel.metadata`` thấy tất cả bảng
(Alembic, ``create_all`` trong test đều dựa vào điều đó).
"""

from app.models.entities import (
    Class,
    Course,
    Enrollment,
    Lesson,
    Problem,
    Submission,
    Testcase,
    User,
)

__all__ = [
    "Class",
    "Course",
    "Enrollment",
    "Lesson",
    "Problem",
    "Submission",
    "Testcase",
    "User",
]
