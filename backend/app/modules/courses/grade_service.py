from uuid import UUID

from sqlalchemy import Row, case
from sqlmodel import Session, func, select

from app.models import Problem, Submission

MAX_SCORE_PER_PROBLEM = 10


def problem_score(problem: Problem, passed: int | None) -> float | None:
    if passed is None or not problem.total_number_testcase:
        return None
    return round(MAX_SCORE_PER_PROBLEM * passed / problem.total_number_testcase, 1)


def best_grade_scores(
    session: Session, problem_ids: list[int], student_ids: list[UUID] | None = None
) -> dict[tuple[UUID, int], Row]:
    """1 truy vấn: bài nộp được chấm điểm của mỗi (sinh viên, bài), chọn bằng window function.

    Ưu tiên: có điểm tay > passed_count cao hơn > nộp muộn hơn > submission_id lớn hơn.
    Chỉ lấy các cột cần cho bảng điểm (không kéo submitted_code, testcase_results...).
    """
    if not problem_ids:
        return {}
    if student_ids is not None and not student_ids:
        return {}
    has_manual_score = case((Submission.manual_score.is_(None), 0), else_=1)
    ranked = select(
        Submission.submission_id,
        Submission.student_id,
        Submission.problem_id,
        Submission.passed_count,
        Submission.manual_score,
        Submission.feedback,
        Submission.status,
        Submission.submitted_datetime,
        func.row_number()
        .over(
            partition_by=(Submission.student_id, Submission.problem_id),
            order_by=(
                has_manual_score.desc(),
                Submission.passed_count.desc(),
                Submission.submitted_datetime.desc(),
                Submission.submission_id.desc(),
            ),
        )
        .label("rn"),
    ).where(Submission.problem_id.in_(problem_ids))
    if student_ids is not None:
        ranked = ranked.where(Submission.student_id.in_(student_ids))
    subquery = ranked.subquery()
    statement = select(
        subquery.c.submission_id,
        subquery.c.student_id,
        subquery.c.problem_id,
        subquery.c.passed_count,
        subquery.c.manual_score,
        subquery.c.feedback,
        subquery.c.status,
        subquery.c.submitted_datetime,
    ).where(subquery.c.rn == 1)
    return {(row.student_id, row.problem_id): row for row in session.exec(statement).all()}


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
            "student_code": student.student_code,
            "full_name": student.full_name,
            "class_id": student.class_id,
            "overall_score": round(total, 1) if has_any else None,
            "session_scores": session_scores,
        })
    return rows
