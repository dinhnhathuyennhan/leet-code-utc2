from fastapi import APIRouter

from app.api import (
    auth,
    classrooms,
    courses,
    enrollments,
    lessons,
    problems,
    students,
    submissions,
    testcases,
    users,
)

api_router = APIRouter()

api_router.include_router(users.router)
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(students.router)
api_router.include_router(enrollments.router)
api_router.include_router(lessons.router)
api_router.include_router(problems.router)
api_router.include_router(submissions.router)
api_router.include_router(classrooms.router)
api_router.include_router(testcases.router)
