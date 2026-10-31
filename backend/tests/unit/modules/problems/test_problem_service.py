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
    AdminTestcaseMutation,
    ProblemTestcaseUpdate,
    ProblemUpdateRequest,
)
from app.modules.problems import service as problem_service
from app.modules.submissions.judge0 import service as judge_service
from app.modules.submissions.judge0.judge0_client import Judge0Result
from app.modules.submissions.judge0.schemas import CodeRequest
from app.models.entities import Problem, Submission, Testcase as CaseModel

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


class TestBankProblemDetail:
    def test_listed_attached_problem_opens_by_id_for_admin_and_owner(
        self, session, problem_factory, problem_lesson, problem_course,
        problem_admin, problem_teacher, problem_other_teacher,
    ):
        attached = problem_factory(problem_lesson)
        for viewer in (problem_admin, problem_teacher):
            detail = problem_service.get_bank_problem(session, attached.problem_id, viewer)
            assert detail.id == attached.problem_id
            assert detail.lesson_id == problem_lesson.lesson_id
            assert detail.course_id == problem_course.course_id
            assert detail.description == attached.description

        with pytest.raises(ForbiddenError):
            problem_service.get_bank_problem(session, attached.problem_id, problem_other_teacher)

    def test_source_problem_opens_by_id_and_missing_id_returns_404(
        self, session, problem_bank_problem, problem_admin,
    ):
        detail = problem_service.get_bank_problem(session, problem_bank_problem.problem_id, problem_admin)
        assert detail.lesson_id is None and detail.course_id is None

        with pytest.raises(NotFoundError):
            problem_service.get_bank_problem(session, 999999, problem_admin)


class TestAdminProblemTestcasesAndPreview:
    def test_source_and_attached_case_crud_preserve_format_and_count(
        self, session, problem_bank_problem, problem_record, problem_admin,
        problem_testcase_factory,
    ):
        for problem in (problem_bank_problem, problem_record):
            problem.function_name = None
            session.add(problem)
            session.flush()
            first = problem_testcase_factory(
                problem, input_type="stdin", expected_output_type="stdout",
                input_value="1 2\n", expected_output="3\n",
            )
            added = problem_service.add_admin_testcase(
                session, problem.problem_id,
                AdminTestcaseMutation(input="2 3\n", expected_output="5\n", input_type="stdin", expected_output_type="stdout"),
                problem_admin,
            )
            assert added.total_number_testcase == 2
            legacy = next(case for case in added.testcases if case.id != first.testcase_id)
            assert legacy.input == "2 3\n" and legacy.expected_output == "5\n"

            updated = problem_service.update_admin_testcase(
                session, problem.problem_id, legacy.id,
                AdminTestcaseMutation(input="3 4\n", expected_output="7\n", is_sample=True, input_type="stdin", expected_output_type="stdout"),
                problem_admin,
            )
            assert next(case for case in updated.testcases if case.id == legacy.id).is_sample
            assert next(case for case in updated.testcases if case.id == legacy.id).input == "3 4\n"

            problem_service.delete_admin_testcase(session, problem.problem_id, first.testcase_id)
            assert problem_service.get_bank_problem(session, problem.problem_id, problem_admin).total_number_testcase == 1
            with pytest.raises(ConflictError):
                problem_service.delete_admin_testcase(session, problem.problem_id, legacy.id)

    def test_function_problem_accepts_json_only(self, session, problem_bank_problem, problem_admin):
        with pytest.raises(InvalidFormatError):
            problem_service.add_admin_testcase(
                session, problem_bank_problem.problem_id,
                AdminTestcaseMutation(input="1\n", expected_output="2\n", input_type="stdin", expected_output_type="stdout"),
                problem_admin,
            )
        detail = problem_service.add_admin_testcase(
            session, problem_bank_problem.problem_id,
            AdminTestcaseMutation(input=[1], expected_output=2), problem_admin,
        )
        assert detail.testcases[0].input == [1]
        assert detail.testcases[0].input_type == "json_args"

    def test_case_changes_reject_existing_submission(
        self, session, problem_record, problem_admin, problem_student,
        problem_testcase_factory, problem_submission_factory,
    ):
        problem_testcase_factory(problem_record)
        problem_submission_factory(problem_record, problem_student)
        with pytest.raises(ConflictError):
            problem_service.add_admin_testcase(
                session, problem_record.problem_id,
                AdminTestcaseMutation(input=[1], expected_output=2), problem_admin,
            )

    def test_preview_runs_all_cases_without_creating_submission(
        self, session, problem_record, problem_admin, problem_testcase_factory, monkeypatch,
    ):
        problem_testcase_factory(problem_record, is_sample=True)
        problem_testcase_factory(problem_record, input_value="[3,4]", expected_output="7", is_sample=False)
        seen = {}

        def fake_judge(problem, data, testcases, timeout):
            seen["ids"] = [case.testcase_id for case in testcases]
            return [
                (Judge0Result(str(index), 3, str(index), None, None, None, 0.1, None), "accepted", index)
                for index, _case in enumerate(testcases, start=1)
            ]

        monkeypatch.setattr(judge_service, "_run_judge", fake_judge)
        response = judge_service.run_admin_preview(
            session, problem_record.problem_id, CodeRequest(language="python", code="def two_sum(): pass"), problem_admin,
        )
        assert response.status == "accepted"
        assert [case.index for case in response.cases] == [1, 2]
        assert len(seen["ids"]) == 2
        assert response.cases[1].input == [3, 4]
        assert session.exec(select(Submission).where(Submission.problem_id == problem_record.problem_id)).all() == []


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


class TestUpdateProblemWithSubmissions:
    """Bài đã có bài nộp vẫn phải sửa được phần nội dung; chỉ chặn khi đổi thứ ảnh hưởng chấm."""

    @pytest.fixture
    def graded_problem(
        self,
        problem_record,
        problem_student,
        problem_submission_factory,
        problem_testcase_factory,
    ):
        problem_testcase_factory(problem_record)
        problem_submission_factory(problem_record, problem_student)
        return problem_record

    def test_resending_unchanged_grading_fields_is_not_a_conflict(
        self, session, problem_teacher, problem_course, problem_lesson, graded_problem
    ):
        # Form gửi lại nguyên trạng mọi trường trong mỗi lần lưu, kể cả khi chỉ sửa mô tả.
        result = problem_service.update_problem(
            session,
            problem_course.course_id,
            problem_lesson.lesson_id,
            graded_problem.problem_id,
            ProblemUpdateRequest(
                description="Mô tả đã sửa",
                function_name=graded_problem.function_name,
                time_limit_seconds=graded_problem.time_limit_seconds,
                starter_codes=dict(graded_problem.starter_codes),
                testcases=[ProblemTestcaseUpdate(input=[[2, 7, 11, 15], 9], expected_output=[0, 1])],
            ),
            problem_teacher,
        )

        assert result.description == "Mô tả đã sửa"

    def test_changing_time_limit_still_conflicts(
        self, session, problem_teacher, problem_course, problem_lesson, graded_problem
    ):
        with pytest.raises(ConflictError, match="ảnh hưởng đến chấm"):
            problem_service.update_problem(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                graded_problem.problem_id,
                ProblemUpdateRequest(time_limit_seconds=graded_problem.time_limit_seconds + 1),
                problem_teacher,
            )

    def test_changing_testcase_content_still_conflicts(
        self, session, problem_teacher, problem_course, problem_lesson, graded_problem
    ):
        with pytest.raises(ConflictError, match="ảnh hưởng đến chấm"):
            problem_service.update_problem(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                graded_problem.problem_id,
                ProblemUpdateRequest(
                    testcases=[ProblemTestcaseUpdate(input=[[1, 2], 3], expected_output=[0, 1])]
                ),
                problem_teacher,
            )

    def test_adding_a_testcase_still_conflicts(
        self, session, problem_teacher, problem_course, problem_lesson, graded_problem
    ):
        with pytest.raises(ConflictError, match="ảnh hưởng đến chấm"):
            problem_service.update_problem(
                session,
                problem_course.course_id,
                problem_lesson.lesson_id,
                graded_problem.problem_id,
                ProblemUpdateRequest(
                    testcases=[
                        ProblemTestcaseUpdate(input=[[2, 7, 11, 15], 9], expected_output=[0, 1]),
                        ProblemTestcaseUpdate(input=[[1, 2], 3], expected_output=[0, 1]),
                    ]
                ),
                problem_teacher,
            )


class TestProblemDetailSubmittedCount:
    def test_teacher_sees_submission_count(
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

        result = problem_service.get_problem_detail(
            session,
            problem_course.course_id,
            problem_lesson.lesson_id,
            problem_record.problem_id,
            problem_teacher,
        )

        assert result.submitted_count == 1

    def test_student_never_sees_submission_count(
        self,
        session,
        problem_student,
        problem_course,
        problem_lesson,
        problem_record,
        problem_enrollment_factory,
        problem_submission_factory,
    ):
        problem_enrollment_factory(problem_course, problem_student)
        problem_submission_factory(problem_record, problem_student)

        result = problem_service.get_problem_detail(
            session,
            problem_course.course_id,
            problem_lesson.lesson_id,
            problem_record.problem_id,
            problem_student,
        )

        assert result.submitted_count is None
