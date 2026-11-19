import { describe, expect, it } from "vitest";
import { buildBreadcrumbs } from "./breadcrumbs";

describe("Teacher breadcrumbs", () => {
  it("shows session title then problem title on a problem page", () => {
    expect(
      buildBreadcrumbs("/teacher/courses/DEMO/sessions/2/problems/4", { course: "DEMO", session: "Mảng và chuỗi", page: "Đảo ngược mảng" }),
    ).toEqual([
      { label: "Lớp học phần", href: "/teacher/courses" },
      { label: "DEMO", href: "/teacher/courses/DEMO" },
      { label: "Mảng và chuỗi", href: "/teacher/courses/DEMO/sessions/2" },
      { label: "Đảo ngược mảng" },
    ]);
  });

  it("shows course, session and submission on a grading page", () => {
    expect(
      buildBreadcrumbs("/teacher/submissions/24", { course: "DEMO", session: "Buổi 1: Nhập môn", page: "SUM · Bài nộp #24" }),
    ).toEqual([
      { label: "Bài nộp", href: "/teacher/submissions" },
      { label: "DEMO", href: "/teacher/courses/DEMO" },
      { label: "Buổi 1: Nhập môn" },
      { label: "SUM · Bài nộp #24" },
    ]);
  });

  it("falls back to the submission id while data is loading", () => {
    expect(buildBreadcrumbs("/teacher/submissions/24", { course: null, session: null })).toEqual([
      { label: "Bài nộp", href: "/teacher/submissions" },
      { label: "#24" },
    ]);
  });
});
