"""Tập hợp mọi model SQLModel.

Import package này là đủ để ``SQLModel.metadata`` thấy tất cả bảng
(Alembic, ``create_all`` trong test đều dựa vào điều đó).
"""

from app.models.entities import (
    AIReviewUsage,
    Class,
    Course,
    Enrollment,
    Lesson,
    LoginAttempt,
    Problem,
    Submission,
    Testcase,
    User,
)

__all__ = [
    "AIReviewUsage",
    "Class",
    "Course",
    "Enrollment",
    "Lesson",
    "LoginAttempt",
    "Problem",
    "Submission",
    "Testcase",
    "User",
]
