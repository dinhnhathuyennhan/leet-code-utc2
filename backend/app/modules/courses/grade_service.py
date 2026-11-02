from uuid import UUID
from sqlmodel import Session, func, select

from app.models import Problem, Submission

MAX_SCORE_PER_PROBLEM = 10


def best_passed_counts(
    session: Session, problem_ids: list[int], student_ids: list[UUID] | None = None
) -> dict[tuple[UUID, int], int]:
    """1 truy vấn: passed_count cao nhất của mỗi (sinh viên, bài)."""
    if not problem_ids:
        return {}
    stmt = (
        select(Submission.student_id, Submission.problem_id, func.max(Submission.passed_count))
        .where(Submission.problem_id.in_(problem_ids))
        .group_by(Submission.student_id, Submission.problem_id)
    )
    if student_ids is not None:
        if not student_ids:
            return {}
        stmt = stmt.where(Submission.student_id.in_(student_ids))
    return {(sid, pid): cnt for sid, pid, cnt in session.exec(stmt).all()}


def problem_score(problem: Problem, passed: int | None) -> float | None:
    if passed is None or not problem.total_number_testcase:
        return None
    return round(MAX_SCORE_PER_PROBLEM * passed / problem.total_number_testcase, 1)


def best_grade_scores(
    session: Session, problem_ids: list[int], student_ids: list[UUID] | None = None
) -> dict[tuple[UUID, int], Submission]:
    if not problem_ids:
        return {}
    statement = select(Submission).where(Submission.problem_id.in_(problem_ids))
    if student_ids is not None:
        statement = statement.where(Submission.student_id.in_(student_ids))
    submissions = list(session.exec(statement).all())
    selected: dict[tuple[UUID, int], Submission] = {}
    for submission in submissions:
        key = (submission.student_id, submission.problem_id)
        current = selected.get(key)
        candidate_key = (submission.manual_score is not None, submission.passed_count, submission.submitted_datetime, submission.submission_id or 0)
        current_key = None if current is None else (current.manual_score is not None, current.passed_count, current.submitted_datetime, current.submission_id or 0)
        if current_key is None or candidate_key > current_key:
            selected[key] = submission
    return selected


def participants_by_lesson(session: Session, lesson_ids: list[int]) -> dict[int, int]:
    if not lesson_ids:
        return {}
    rows = session.exec(
        select(Problem.lesson_id, func.count(func.distinct(Submission.student_id)))
        .select_from(Problem)
        .join(Submission, Submission.problem_id == Problem.problem_id)
        .where(Problem.lesson_id.in_(lesson_ids))
        .group_by(Problem.lesson_id)
    ).all()
    return dict(rows)


def build_grade_rows(lessons, problems_by_lesson, enrollments, best) -> list[dict]:
    rows = []
    for _enrollment, student in enrollments:
        session_scores: dict[str, list[dict]] = {}
        total, has_any = 0.0, False
        for lesson in lessons:
            cells = []
            for problem in problems_by_lesson.get(lesson.lesson_id, []):
                submission = best.get((student.user_id, problem.problem_id))
                passed = submission.passed_count if submission else None
                score = submission.manual_score if submission and submission.manual_score is not None else problem_score(problem, passed)
                if score is not None:
                    total += score
                    has_any = True
                cells.append({
                    "value": score,
                    "submitted": submission is not None,
                    "manual_score": submission.manual_score if submission else None,
                    "is_overridden": bool(submission and submission.manual_score is not None),
                    "feedback": submission.feedback if submission else None,
                    "submission_id": submission.submission_id if submission else None,
                    "status": submission.status if submission else None,
                    "submitted_datetime": submission.submitted_datetime if submission else None,
                })
            session_scores[str(lesson.lesson_id)] = cells
        rows.append({
            "student_id": str(student.user_id),
            "full_name": student.full_name,
            "class_id": student.class_id,
            "overall_score": round(total, 1) if has_any else None,
            "session_scores": session_scores,
        })
    return rows
