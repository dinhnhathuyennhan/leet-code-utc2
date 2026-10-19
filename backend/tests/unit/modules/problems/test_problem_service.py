from datetime import datetime

import pytest
from sqlmodel import select

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.core.utils.datetime_utils import VN_TZ
from app.modules.problems.schemas import (
    ProblemTestcaseUpdate,
    ProblemUpdateRequest,
)
from app.modules.problems import service as problem_service
from app.models.entities import Problem, Testcase as CaseModel

pytest_plugins = ("tests.support.fixtures.problem_fixtures",)


class TestCreateBankProblem:
    def test_create_bank_problem_stores_nullable_lesson_and_json_testcase(
        self, session, problem_create_request_factory
    ):
        result = problem_service.create_bank_problem(
            session, problem_create_request_factory()
        )

        saved = session.get(Problem, result.id)
        testcase = session.exec(
            select(CaseModel).where(CaseModel.problem_id == result.id)
        ).one()
        assert saved.lesson_id is None
        assert result.lesson_id is None and result.course_id is None
        assert saved.title == "Bank Problem"
        assert saved.total_number_testcase == 1
        assert testcase.input == "[1,2]"
        assert testcase.expected_output == "3"
        assert result.testcases[0].input == [1, 2]


class TestListProblems:
    def test_list_problems_scopes_teacher_to_bank_and_owned_lessons_and_applies_filters(
        self,
        session,
        problem_teacher,
        problem_other_teacher,
        problem_course,
        problem_lesson,
        problem_other_lesson,
        problem_factory,
        problem_bank_problem,
    ):
        own = problem_factory(problem_lesson, title="Own Two Sum")
        problem_factory(problem_other_lesson, title="Other Course Two Sum")
        problem_factory(None, title="Bank Three Sum", level="medium")

        result = problem_service.list_problems(
            session,
            problem_teacher,
            q="two sum",
            level="easy",
            course_id=None,
            page=1,
            page_size=1,
        )
        assert result.total == 2
        assert result.items[0].id == own.problem_id
        assert result.page == 1 and result.page_size == 1

        bank = problem_service.list_problems(
            session,
            problem_teacher,
            q="Three",
            level=None,
            course_id=None,
            page=1,
            page_size=10,
        )
        assert [item.title for item in bank.items] == ["Bank Three Sum"]

    def test_list_problems_allows_admin_and_course_filter_including_empty_search(
        self,
        session,
        problem_admin,
        problem_course,
        problem_lesson,
        problem_other_lesson,
        problem_factory,
    ):
        in_course = problem_factory(problem_lesson)
        problem_factory(problem_other_lesson, title="Other")
        problem_factory(None, title="Bank")

        result = problem_service.list_problems(
            session,
            problem_admin,
            q="   ",
            level=None,
            course_id=problem_course.course_id,
            page=1,
            page_size=20,
        )
        assert result.total == 1
        assert result.items[0].id == in_course.problem_id


class TestCopyProblemsToLesson:
    def test_copy_problems_clones_bank_content_and_skips_problem_already_in_target_lesson(
        self,
        session,
        problem_teacher,
        problem_lesson,
        problem_record,
        problem_bank_problem,
        problem_testcase_factory,
    ):
        problem_testcase_factory(problem_record)
        problem_testcase_factory(problem_bank_problem, is_sample=True)

        copied = problem_service.copy_problems_to_lesson(
            session,
            [problem_record.problem_id, problem_bank_problem.problem_id],
            problem_lesson,
            problem_teacher,
        )

        assert copied[0].problem_id == problem_record.problem_id
        assert copied[1].problem_id != problem_bank_problem.problem_id
        assert copied[1].lesson_id == problem_lesson.lesson_id
        assert copied[1].total_number_testcase == 1
        clone_case = session.exec(
            select(CaseModel).where(CaseModel.problem_id == copied[1].problem_id)
        ).one()
        assert clone_case.is_sample

    def test_copy_problems_rejects_unknown_id_missing_testcases_and_foreign_lesson(
        self,
        session,
        problem_teacher,
        problem_other_teacher,
        problem_lesson,
        problem_other_lesson,
        problem_factory,
        problem_testcase_factory,
    ):
        with pytest.raises(NotFoundError, match="không tồn tại"):
            problem_service.copy_problems_to_lesson(
                session, [999999], problem_lesson, problem_teacher
            )

        empty_bank_problem = problem_factory(None)
        with pytest.raises(InvalidFormatError, match="ít nhất một testcase"):
            problem_service.copy_problems_to_lesson(
                session,
                [empty_bank_problem.problem_id],
                problem_lesson,
                problem_teacher,
            )

        foreign_problem = problem_factory(problem_other_lesson)
        problem_testcase_factory(foreign_problem)
        with pytest.raises(ForbiddenError, match="không có quyền sao chép"):
            problem_service.copy_problems_to_lesson(
                session, [foreign_problem.problem_id], problem_lesson, problem_teacher
            )

    def test_admin_can_copy_foreign_lesson_problem(
        self,
        session,
        problem_admin,
        problem_lesson,
        problem_other_lesson,
        problem_factory,
        problem_testcase_factory,
    ):
        source = problem_factory(problem_other_lesson)
        problem_testcase_factory(source)
        result = problem_service.copy_problems_to_lesson(
            session, [source.problem_id], problem_lesson, problem_admin
        )
        assert result[0].lesson_id == problem_lesson.lesson_id

    def test_admin_copy_of_missing_problem_returns_not_found(
        self, session, problem_admin, problem_lesson
    ):
        with pytest.raises(NotFoundError, match="Một hoặc nhiều bài tập không tồn tại"):
            problem_service.copy_problems_to_lesson(
                session, [99999], problem_lesson, problem_admin
            )


class TestGetProblemDetail:
    def test_student_problem_detail_hides_future_problem_and_hidden_testcases(
        self,
        session,
        problem_student,
        problem_course,
        problem_lesson,
        problem_enrollment_factory,
        problem_factory,
        problem_testcase_factory,
    ):
        from datetime import timedelta

        problem_enrollment_factory(problem_course, problem_student)
        problem = problem_factory(problem_lesson)
        problem_testcase_factory(problem, is_sample=True)
        problem_testcase_factory(problem, input_value="[2]", is_sample=False)
        detail = problem_service.get_problem_detail(
            session,
            problem_course.course_id,
            problem_lesson.lesson_id,
            problem.problem_id,
            problem_student,
        )
        assert len(detail.testcases) == 1
        assert detail.testcases[0].is_sample

        future = problem_factory(
            problem_lesson,
            title="Not open yet",
            start_datetime=datetime.now(VN_TZ) + timedelta(days=30),
        )
        with pytest.raises(NotFoundError, match="Không tìm thấy bài tập"):
            problem_service.get_problem_detail(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                future.problem_id,
                problem_student,
            )

    def test_problem_detail_rejects_a_problem_attached_to_a_different_lesson(
        self,
        session,
        problem_admin,
        problem_course,
        problem_lesson,
        problem_other_lesson,
        problem_factory,
    ):
        foreign = problem_factory(problem_other_lesson)
        with pytest.raises(NotFoundError, match="Không tìm thấy bài tập"):
            problem_service.get_problem_detail(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                foreign.problem_id,
                problem_admin,
            )


class TestUpdateProblem:
    def test_update_problem_supports_nullable_metadata_and_legacy_python_template(
        self, session, problem_teacher, problem_course, problem_lesson, problem_record
    ):
        result = problem_service.update_problem(
            session,
            problem_course.course_id,
            problem_lesson.lesson_id,
            problem_record.problem_id,
            ProblemUpdateRequest(
                hint=None, complexity=None, report=None, starter_code="legacy template"
            ),
            problem_teacher,
        )
        session.refresh(problem_record)
        assert (
            problem_record.hint is None
            and problem_record.complexity is None
            and problem_record.report is None
        )
        assert problem_record.starter_codes["python"] == "legacy template"
        assert result.starter_code == "legacy template"

    def test_update_problem_replaces_testcases_and_keeps_starter_codes_in_sync(
        self,
        session,
        problem_teacher,
        problem_course,
        problem_lesson,
        problem_record,
        problem_testcase_factory,
    ):
        problem_testcase_factory(problem_record)
        new_codes = {
            "python": "def two_sum(): pass",
            "c": "int two_sum(void) { return 0; }",
            "cpp": "int two_sum() { return 0; }",
            "java": "class Solution { int two_sum() { return 0; } }",
        }
        result = problem_service.update_problem(
            session,
            problem_course.course_id,
            problem_lesson.lesson_id,
            problem_record.problem_id,
            ProblemUpdateRequest(
                starter_codes=new_codes,
                testcases=[
                    ProblemTestcaseUpdate(input=[5], expected_output=5, is_sample=True)
                ],
            ),
            problem_teacher,
        )
        session.refresh(problem_record)
        cases = session.exec(
            select(CaseModel).where(CaseModel.problem_id == problem_record.problem_id)
        ).all()
        assert problem_record.starter_codes == new_codes
        assert problem_record.start_format_code == new_codes["python"]
        assert problem_record.total_number_testcase == 1
        assert len(cases) == 1 and cases[0].input == "[5]"
        assert result.testcases[0].expected_output == 5

    def test_update_problem_rejects_grading_metadata_changes_after_submission_without_mutating_problem(
        self,
        session,
        problem_teacher,
        problem_student,
        problem_course,
        problem_lesson,
        problem_record,
        problem_submission_factory,
    ):
        problem_submission_factory(problem_record, problem_student)
        original_starter_codes = problem_record.starter_codes.copy()
        updated_starter_codes = {
            "python": "class Solution: pass",
            "c": "int twoSum(void) { return 0; }",
            "cpp": "int twoSum() { return 0; }",
            "java": "class Solution { int twoSum() { return 0; } }",
        }

        with pytest.raises(ConflictError, match="ảnh hưởng đến chấm"):
            problem_service.update_problem(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                problem_record.problem_id,
                ProblemUpdateRequest(
                    function_name="two_sum_v2",
                    time_limit_seconds=3,
                    starter_codes=updated_starter_codes,
                ),
                problem_teacher,
            )
        session.refresh(problem_record)
        assert problem_record.time_limit_seconds == 2
        assert problem_record.function_name == "two_sum"
        assert problem_record.starter_codes == original_starter_codes

    def test_update_problem_rejects_invalid_schedule_before_saving_new_values(
        self, session, problem_teacher, problem_course, problem_lesson, problem_record
    ):
        with pytest.raises(InvalidFormatError, match="start_datetime"):
            problem_service.update_problem(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                problem_record.problem_id,
                ProblemUpdateRequest(start_datetime=datetime(2027, 1, 1, tzinfo=VN_TZ)),
                problem_teacher,
            )
        session.refresh(problem_record)
        assert problem_record.start_datetime == datetime(2026, 1, 1, tzinfo=VN_TZ)


class TestReplaceTestcases:
    def test_replace_testcases_updates_case_count(
        self,
        session,
        problem_teacher,
        problem_course,
        problem_lesson,
        problem_record,
        problem_testcase_factory,
    ):
        problem_testcase_factory(problem_record)
        problem_service.replace_testcases(
            session,
            problem_course.course_id,
            problem_lesson.lesson_id,
            problem_record.problem_id,
            [{"input": [3], "expected_output": 9, "is_sample": True}],
            problem_teacher,
        )
        session.refresh(problem_record)
        assert problem_record.total_number_testcase == 1

    def test_replace_testcases_is_locked_after_submission(
        self,
        session,
        problem_teacher,
        problem_student,
        problem_course,
        problem_lesson,
        problem_record,
        problem_submission_factory,
    ):
        problem_submission_factory(problem_record, problem_student)
        with pytest.raises(ConflictError, match="không thể thay đổi testcase"):
            problem_service.replace_testcases(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                problem_record.problem_id,
                [{"input": [1], "expected_output": 1, "is_sample": False}],
                problem_teacher,
            )


class TestDeleteProblem:
    def test_delete_problem_removes_problem_and_its_testcases(
        self,
        session,
        problem_teacher,
        problem_course,
        problem_lesson,
        problem_record,
        problem_testcase_factory,
    ):
        problem_testcase_factory(problem_record)
        problem_service.delete_problem(
            session,
            problem_course.course_id,
            problem_lesson.lesson_id,
            problem_record.problem_id,
            problem_teacher,
        )
        assert session.get(Problem, problem_record.problem_id) is None
        assert (
            session.exec(
                select(CaseModel).where(
                    CaseModel.problem_id == problem_record.problem_id
                )
            ).all()
            == []
        )
        assert problem_lesson.total_number_assignment == 0

    def test_delete_problem_rejects_problem_with_submission(
        self,
        session,
        problem_teacher,
        problem_student,
        problem_course,
        problem_lesson,
        problem_record,
        problem_submission_factory,
    ):
        problem_submission_factory(problem_record, problem_student)
        with pytest.raises(ConflictError, match="không thể xoá"):
            problem_service.delete_problem(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                problem_record.problem_id,
                problem_teacher,
            )
