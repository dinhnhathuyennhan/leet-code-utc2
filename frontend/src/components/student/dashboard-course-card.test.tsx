/**
 * Unit tests cho DashboardCourseCard — kiểm tra refactor theo Figma:
 *  - Toàn bộ card là 1 Link duy nhất
 *  - KHÔNG còn nút "Chi tiết" / "Vào học" ở footer
 *  - KHÔNG còn logo chữ ở góc trên bên phải banner
 *  - Có badge trạng thái + mã lớp + tên lớp
 *  - Footer mới: tên GV trái, icon chat + members phải
 */
import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";

import { DashboardCourseCard, resolveLanguage } from "./dashboard-course-card";
import type { CourseSummary } from "@/lib/types/course";

const baseCourse: CourseSummary = {
  id: "CS101",
  code: "CS101.K64",
  name: "Nhập môn lập trình",
  term: "2024-2025 - HK1",
  start_date: "2024-09-01",
  end_date: "2025-01-15",
  avt_link: null,
  created_by: "Nguyễn Văn A",
  total_number_student: 60,
};

function renderCard(overrides: Partial<React.ComponentProps<typeof DashboardCourseCard>> = {}) {
  return render(
    <DashboardCourseCard
      course={baseCourse}
      language="Java"
      teacherName="Nguyễn Văn A"
      status="ongoing"
      messageCount={3}
      memberCount={60}
      href="/student/classes/CS101"
      {...overrides}
    />,
  );
}

describe("DashboardCourseCard", () => {
  it("renders as a single Link to the course href", () => {
    renderCard();
    const link = screen.getByRole("link", { name: /CS101/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/student/classes/CS101");
  });

  it("does NOT render the old 'Chi tiết' / 'Vào học' action buttons", () => {
    renderCard();
    expect(screen.queryByRole("button", { name: /chi tiết/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /vào học/i })).toBeNull();
  });

  it("does NOT render a logo badge in the top-right of the banner", () => {
    const { container } = renderCard();
    const banner = container.querySelector(".h-32");
    expect(banner).toBeInTheDocument();
    // Old code had a `absolute right-4 top-4` logo badge. Make sure no small text sits there.
    const cornerBadges = banner?.querySelectorAll(".absolute.right-4.top-4");
    expect(cornerBadges?.length ?? 0).toBe(0);
  });

  it("displays the status badge, course code, and course name", () => {
    renderCard({ status: "ongoing" });
    const link = screen.getByRole("link");
    expect(within(link).getByText("Đang diễn ra")).toBeInTheDocument();
    expect(within(link).getByText("CS101.K64")).toBeInTheDocument();
    expect(within(link).getByText("Nhập môn lập trình")).toBeInTheDocument();
  });

  it("renders the teacher name + message and member counts in footer", () => {
    renderCard({ messageCount: 7, memberCount: 42 });
    expect(screen.getByText(/Nguyễn Văn A/)).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("shows different status labels and themes by status", () => {
    const { rerender } = renderCard({ status: "upcoming" });
    expect(screen.getByText("Sắp khai giảng")).toBeInTheDocument();
    rerender(
      <DashboardCourseCard
        course={baseCourse}
        language="Java"
        status="closed"
        href="/student/classes/CS101"
      />,
    );
    expect(screen.getByText("Đã kết thúc")).toBeInTheDocument();
  });

  it("uses course.created_by when teacherName is empty/undefined", () => {
    // Logic hiện tại: `teacherName?.trim() || course.created_by || "Giảng viên UTC2"`
    // → teacherName rỗng fallback về created_by, KHÔNG phải 'Giảng viên UTC2'
    const { rerender } = renderCard({ teacherName: undefined });
    expect(screen.getByText(/Nguyễn Văn A/)).toBeInTheDocument();

    rerender(
      <DashboardCourseCard
        course={baseCourse}
        language="Java"
        teacherName=""
        status="ongoing"
        href="/student/classes/CS101"
      />,
    );
    expect(screen.getByText(/Nguyễn Văn A/)).toBeInTheDocument();
  });

  it("falls back to 'Giảng viên UTC2' when BOTH teacherName and created_by are empty", () => {
    const courseNoTeacher: CourseSummary = { ...baseCourse, created_by: "" };
    render(
      <DashboardCourseCard
        course={courseNoTeacher}
        language="Java"
        status="ongoing"
        href="/student/classes/CS101"
      />,
    );
    expect(screen.getByText(/Giảng viên UTC2/)).toBeInTheDocument();
  });
});

describe("resolveLanguage", () => {
  it.each([
    ["Java", "java"],
    ["JAVA", "java"],
    ["Python", "python"],
    ["JavaScript", "javascript"],
    ["JS", "javascript"],
    ["C++", "cpp"],
    ["cpp", "cpp"],
    ["C", "c"],
    ["Go", "go"],
    ["Rust", "default"],
    [undefined, "default"],
  ])('resolveLanguage("%s") → %s', (input, expected) => {
    expect(resolveLanguage(input)).toBe(expected);
  });
});
