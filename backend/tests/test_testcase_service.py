import json
import zipfile
from io import BytesIO

import pytest
from sqlmodel import select

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.schemas.problem import ProblemTestcaseUpdate
from app.schemas.testcase import (
    TestcaseBatchRequest as BatchRequest,
    TestcasePreviewRequest as PreviewRequest,
    TestcaseUpdateRequest as UpdateRequest,
)
from app.services import testcase_service
from models import Testcase as CaseModel

pytest_plugins = ("fixtures.testcase_fixtures",)


class TestListTestcases:
    def test_student_testcase_list_always_returns_samples_even_when_hidden_filter_requested(
        self,
        session,
        testcase_student,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
        testcase_enrollment_factory,
    ):
        testcase_enrollment_factory(testcase_course, testcase_student)
        testcase_factory(testcase_problem, is_sample=True)
        testcase_factory(
            testcase_problem, input_value="[3]", expected_output="9", is_sample=False
        )

        result = testcase_service.list_testcases(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            False,
            testcase_student,
        )

        assert len(result.testcases) == 1
        assert result.testcases[0].input == [[2, 7, 11, 15], 9]
        assert result.total_sample == 1 and result.total_hidden == 1

    def test_teacher_testcase_list_can_filter_hidden_testcases(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
    ):
        testcase_factory(testcase_problem, is_sample=True)
        hidden = testcase_factory(testcase_problem, input_value="[4]", is_sample=False)

        result = testcase_service.list_testcases(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            False,
            testcase_teacher,
        )

        assert [testcase.id for testcase in result.testcases] == [hidden.testcase_id]
        assert result.total_sample == 1 and result.total_hidden == 1

    def test_teacher_testcase_list_returns_all_cases_when_sample_filter_is_omitted(
        self,
        session,
        testcase_admin,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
    ):
        testcase_factory(testcase_problem, is_sample=True)
        testcase_factory(testcase_problem, input_value="[4]", is_sample=False)

        result = testcase_service.list_testcases(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            None,
            testcase_admin,
        )

        assert len(result.testcases) == 2

    def test_student_cannot_view_testcases_before_problem_opens(
        self,
        session,
        testcase_student,
        testcase_course,
        testcase_lesson,
        testcase_enrollment_factory,
        testcase_problem_factory,
    ):
        from datetime import UTC, datetime, timedelta

        testcase_enrollment_factory(testcase_course, testcase_student)
        future = testcase_problem_factory(
            testcase_lesson,
            start_datetime=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1),
        )
        with pytest.raises(NotFoundError, match="Không tìm thấy bài tập"):
            testcase_service.list_testcases(
                session,
                testcase_course.course_id,
                testcase_lesson.lesson_id,
                future.problem_id,
                None,
                testcase_student,
            )


class TestUpdateTestcase:
    def test_testcase_lookup_rejects_id_from_another_problem(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_problem_factory,
        testcase_factory,
    ):
        other_problem = testcase_problem_factory(testcase_lesson, title="Other problem")
        other_testcase = testcase_factory(other_problem)

        with pytest.raises(NotFoundError, match="Không tìm thấy testcase"):
            testcase_service.update_testcase(
                session,
                testcase_course.course_id,
                testcase_lesson.lesson_id,
                testcase_problem.problem_id,
                other_testcase.testcase_id,
                UpdateRequest(is_sample=True),
                testcase_teacher,
            )

    def test_update_testcase_encodes_changed_values_and_preserves_omitted_fields(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
    ):
        testcase = testcase_factory(testcase_problem, is_sample=False)
        testcase_service.update_testcase(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            testcase.testcase_id,
            UpdateRequest(input=[8], expected_output=None, is_sample=True),
            testcase_teacher,
        )
        session.refresh(testcase)
        assert testcase.input == "[8]" and testcase.input_type == "json_args"
        assert (
            testcase.expected_output == "null"
            and testcase.expected_output_type == "json"
        )
        assert testcase.is_sample is True

    def test_update_testcase_ignores_explicit_null_sample_value(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
    ):
        testcase = testcase_factory(testcase_problem, is_sample=False)
        testcase_service.update_testcase(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            testcase.testcase_id,
            UpdateRequest(is_sample=None),
            testcase_teacher,
        )
        session.refresh(testcase)
        assert testcase.is_sample is False

    def test_update_testcase_is_blocked_after_submission(
        self,
        session,
        testcase_teacher,
        testcase_student,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
        testcase_submission_factory,
    ):
        testcase = testcase_factory(testcase_problem)
        testcase_submission_factory(testcase_problem, testcase_student)
        with pytest.raises(ConflictError, match="không thể thay đổi testcase"):
            testcase_service.update_testcase(
                session,
                testcase_course.course_id,
                testcase_lesson.lesson_id,
                testcase_problem.problem_id,
                testcase.testcase_id,
                UpdateRequest(is_sample=True),
                testcase_teacher,
            )


class TestAddTestcase:
    def test_add_testcase_saves_json_and_refreshes_problem_count(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
    ):
        response = testcase_service.add_testcase(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            ProblemTestcaseUpdate(input=[4, 5], expected_output=9, is_sample=True),
            testcase_teacher,
        )
        session.refresh(testcase_problem)
        saved = session.exec(
            select(CaseModel).where(CaseModel.problem_id == testcase_problem.problem_id)
        ).one()
        assert saved.input == "[4,5]" and saved.expected_output == "9"
        assert testcase_problem.total_number_testcase == 1
        assert response.testcases[0].input == [4, 5]

    def test_add_testcase_requires_course_owner(
        self,
        session,
        testcase_other_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
    ):
        with pytest.raises(ForbiddenError, match="không có quyền"):
            testcase_service.add_testcase(
                session,
                testcase_course.course_id,
                testcase_lesson.lesson_id,
                testcase_problem.problem_id,
                ProblemTestcaseUpdate(input=[], expected_output=0),
                testcase_other_teacher,
            )


class TestDeleteTestcase:
    def test_delete_testcase_is_blocked_after_submission(
        self,
        session,
        testcase_teacher,
        testcase_student,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
        testcase_submission_factory,
    ):
        testcase = testcase_factory(testcase_problem)
        testcase_submission_factory(testcase_problem, testcase_student)
        with pytest.raises(ConflictError, match="không thể thay đổi testcase"):
            testcase_service.delete_testcase(
                session,
                testcase_course.course_id,
                testcase_lesson.lesson_id,
                testcase_problem.problem_id,
                testcase.testcase_id,
                testcase_teacher,
            )

    def test_delete_testcase_requires_at_least_one_case_and_updates_count(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
    ):
        only_case = testcase_factory(testcase_problem)
        with pytest.raises(ConflictError, match="ít nhất một testcase"):
            testcase_service.delete_testcase(
                session,
                testcase_course.course_id,
                testcase_lesson.lesson_id,
                testcase_problem.problem_id,
                only_case.testcase_id,
                testcase_teacher,
            )
        second = testcase_factory(testcase_problem, input_value="[2]")
        testcase_service.delete_testcase(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            only_case.testcase_id,
            testcase_teacher,
        )
        session.refresh(testcase_problem)
        assert testcase_problem.total_number_testcase == 1
        assert session.get(CaseModel, second.testcase_id) is not None


class TestBatchUpdateSample:
    def test_batch_update_sample_changes_all_requested_cases_and_rejects_unknown_case(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
    ):
        first = testcase_factory(testcase_problem)
        second = testcase_factory(testcase_problem, input_value="[2]")
        result = testcase_service.batch_update_sample(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            BatchRequest(
                testcase_ids=[first.testcase_id, second.testcase_id], is_sample=True
            ),
            testcase_teacher,
        )
        assert len([case for case in result.testcases if case.is_sample]) == 2

        with pytest.raises(NotFoundError, match="Một hoặc nhiều testcase"):
            testcase_service.batch_update_sample(
                session,
                testcase_course.course_id,
                testcase_lesson.lesson_id,
                testcase_problem.problem_id,
                BatchRequest(testcase_ids=[99999], is_sample=False),
                testcase_teacher,
            )


class TestExportTestcases:
    @pytest.mark.parametrize("export_format", ["json", "zip"])
    def test_export_testcases_preserves_json_and_legacy_formats(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
        testcase_factory,
        export_format,
    ):
        testcase_factory(testcase_problem, is_sample=True)
        legacy = testcase_factory(
            testcase_problem,
            input_value="2 7 9",
            expected_output="0 1",
            input_type="stdin",
            expected_output_type="stdout",
        )
        content = testcase_service.export_testcases(
            session,
            testcase_course.course_id,
            testcase_lesson.lesson_id,
            testcase_problem.problem_id,
            export_format,
            testcase_teacher,
        )

        if export_format == "json":
            payload = json.loads(content)
        else:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                payload = json.loads(
                    archive.read(f"testcases_{testcase_problem.problem_id}.json")
                )
        assert payload["problem_title"] == testcase_problem.title
        assert payload["testcases"][1]["input"] == "2 7 9"
        assert payload["testcases"][1]["expected_output_type"] == "stdout"
        assert legacy.input == "2 7 9"

    def test_export_testcases_rejects_unsupported_format(
        self,
        session,
        testcase_teacher,
        testcase_course,
        testcase_lesson,
        testcase_problem,
    ):
        with pytest.raises(
            testcase_service.InvalidExportFormatError, match=r"json.*zip"
        ):
            testcase_service.export_testcases(
                session,
                testcase_course.course_id,
                testcase_lesson.lesson_id,
                testcase_problem.problem_id,
                "csv",
                testcase_teacher,
            )


class TestPreviewTestcases:
    def test_preview_testcases_reports_each_invalid_item_and_duplicate_output_warning(
        self,
    ):
        response = testcase_service.preview_testcases(
            PreviewRequest(
                testcases=[
                    "not an object",
                    {"input": []},
                    {"input": 1, "expected_output": 1},
                    {"input": [], "expected_output": float("nan")},
                    {"input": [], "expected_output": 1, "is_sample": 1},
                    {"input": [], "expected_output": 1, "input_type": "stdin"},
                    {
                        "input": [],
                        "expected_output": 1,
                        "expected_output_type": "stdout",
                    },
                    {"input": [1], "expected_output": 10, "is_sample": True},
                    {"input": [2], "expected_output": 10, "is_sample": False},
                ]
            )
        )

        assert response.valid is False
        assert [error.index for error in response.errors] == list(range(1, 8))
        assert response.count == 9
        assert response.sample_count == 1 and response.hidden_count == 1
        assert any(
            "cùng expected_output" in warning.message for warning in response.warnings
        )

    def test_preview_testcases_warns_when_valid_items_have_no_sample(self):
        response = testcase_service.preview_testcases(
            PreviewRequest(testcases=[{"input": [], "expected_output": {"ok": True}}])
        )
        assert response.valid
        assert response.sample_count == 0 and response.hidden_count == 1
        assert any(
            "Không có testcase mẫu" in warning.message for warning in response.warnings
        )
