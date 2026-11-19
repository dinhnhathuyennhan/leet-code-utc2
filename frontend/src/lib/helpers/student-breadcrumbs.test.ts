import { describe, expect, it } from "vitest";
import { buildBreadcrumbs } from "./breadcrumbs";

/** Trang sinh viên đặt nhãn trang hiện tại qua `useBreadcrumbLabel` → slot `course`. */
const page = (label: string) => ({ course: label, session: null });

describe("Student breadcrumbs", () => {
  it("labels top-level pages instead of showing an ellipsis", () => {
    expect(buildBreadcrumbs("/student/dashboard")).toEqual([{ label: "Tổng quan" }]);
    expect(buildBreadcrumbs("/student/classes")).toEqual([{ label: "Lớp học phần" }]);
    expect(buildBreadcrumbs("/student/assignments", page("nav.assignments"))).toEqual([{ label: "Bài tập" }]);
    expect(buildBreadcrumbs("/student/history", page("nav.history"))).toEqual([{ label: "Lịch sử nộp bài" }]);
  });

  it("links a class page back to the class list", () => {
    expect(buildBreadcrumbs("/student/classes/DEMO101-2026A", page("DEMO101-2026A"))).toEqual([
      { label: "Lớp học phần", href: "/student/classes" },
      { label: "DEMO101-2026A" },
    ]);
  });

  it("only links to routes that exist on an assignment page", () => {
    expect(buildBreadcrumbs("/student/classes/DEMO101-2026A/assignments/1", page("Tổng hai số"))).toEqual([
      { label: "Lớp học phần", href: "/student/classes" },
      { label: "DEMO101-2026A", href: "/student/classes/DEMO101-2026A" },
      { label: "Tổng hai số" },
    ]);
  });

  it("links a submission result back to the history page", () => {
    expect(buildBreadcrumbs("/student/submissions/22", page("Kết quả #22"))).toEqual([
      { label: "Lịch sử nộp bài", href: "/student/history" },
      { label: "Kết quả #22" },
    ]);
  });

  it("decodes encoded class codes", () => {
    expect(buildBreadcrumbs("/student/classes/A%20B")).toEqual([
      { label: "Lớp học phần", href: "/student/classes" },
      { label: "A B" },
    ]);
  });
});
