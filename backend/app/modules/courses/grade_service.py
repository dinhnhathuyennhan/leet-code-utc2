from sqlmodel import Session, func, select

from app.models import Problem, Submission

MAX_SCORE_PER_PROBLEM = 10


def best_passed_counts(
    session: Session, problem_ids: list[int], student_ids: list[str] | None = None
) -> dict[tuple[str, int], int]:
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
                passed = best.get((student.user_id, problem.problem_id))
                score = problem_score(problem, passed)
                if score is not None:
                    total += score
                    has_any = True
                cells.append({"value": score, "submitted": passed is not None})
            session_scores[str(lesson.lesson_id)] = cells
        rows.append({
            "student_id": student.user_id,
            "full_name": student.full_name,
            "class_id": student.class_id,
            "overall_score": round(total, 1) if has_any else None,
            "session_scores": session_scores,
        })
    return rows
