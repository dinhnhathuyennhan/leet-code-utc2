/**
 * Bảng điểm dùng chung cho giảng viên (ghi đè điểm được) và Admin (`readOnly`: chỉ xem).
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CourseGradesTable } from "./course-grades-table";
import type { GradeRow, GradeSessionColumn } from "@/lib/types/course";

const sessions: GradeSessionColumn[] = [
  { id: 1, order: 1, title: "Nhập môn", status: "open", problems: [{ id: 10, code: "BT-01", title: "Tổng hai số" }] },
];
const rows: GradeRow[] = [{
  student_id: "uuid-1", student_code: "6551071001", full_name: "Nguyễn Văn A", class_id: "CQ.65.CNTT",
  problem_scores: [], overall_score: null,
  session_scores: { "1": [{ value: 7.5, submitted: true, submission_id: 1 }] },
}];

const HINT = "Double click vào ô điểm để ghi đè điểm và thêm nhận xét.";

describe("CourseGradesTable", () => {
  it("lets the teacher open the grade override dialog", async () => {
    render(<CourseGradesTable courseId="CS101" rows={rows} sessions={sessions} />);

    expect(screen.getByText(HINT)).toBeInTheDocument();
    await userEvent.dblClick(screen.getByTitle("Double click để ghi đè điểm"));
    expect(screen.getByRole("heading", { name: "Ghi đè điểm" })).toBeInTheDocument();
  });

  it("is view-only in readOnly mode (Admin)", async () => {
    render(<CourseGradesTable readOnly courseId="CS101" rows={rows} sessions={sessions} />);

    expect(screen.queryByText(HINT)).not.toBeInTheDocument();
    expect(screen.queryByTitle("Double click để ghi đè điểm")).not.toBeInTheDocument();
    await userEvent.dblClick(screen.getAllByText("7.5")[0]);
    expect(screen.queryByRole("heading", { name: "Ghi đè điểm" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Xuất bảng điểm/ })).toBeInTheDocument();
  });
});
