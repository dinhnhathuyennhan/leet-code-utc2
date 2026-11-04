import { describe, expect, it } from "vitest";
import { buildBreadcrumbs } from "./breadcrumbs";

describe("Admin breadcrumbs", () => {
  it("does not create an unknown role crumb linking to /admin", () => {
    expect(buildBreadcrumbs("/admin/accounts/import")).toEqual([
      { label: "Quản lý tài khoản", href: "/admin/accounts" },
      { label: "Nhập từ Excel", href: undefined },
    ]);
  });
  it("keeps course, lesson and problem links inside Admin", () => {
    expect(buildBreadcrumbs("/admin/courses/JAVA01/sessions/2/problems/3", { course: "JAVA01", session: "Mảng", page: "Tổng mảng" })).toEqual([
      { label: "Lớp học phần", href: "/admin/courses" },
      { label: "JAVA01", href: "/admin/courses/JAVA01" },
      { label: "Mảng", href: "/admin/courses/JAVA01/sessions/2" },
      { label: "Tổng mảng" },
    ]);
  });
  it("preserves Teacher course breadcrumbs", () => {
    expect(buildBreadcrumbs("/teacher/courses/JAVA01", { course: "JAVA01", session: null })).toEqual([
      { label: "Lớp học phần", href: "/teacher/courses" },
      { label: "JAVA01", href: undefined },
    ]);
  });
});
