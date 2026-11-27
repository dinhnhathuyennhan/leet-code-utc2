import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { toast } from "sonner";

import { CourseStudentsTable } from "./course-students-table";
import * as adminApi from "@/lib/api/endpoints/admin";
import { ApiError } from "@/lib/api/error";
import type { CourseStudent } from "@/lib/types/course";

vi.mock("@/lib/api/endpoints/admin", () => ({
  importStudents: vi.fn(), lockUser: vi.fn(), unlockUser: vi.fn(), updateUser: vi.fn(),
}));
vi.mock("@/lib/api/endpoints/courses", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api/endpoints/courses")>()),
  addClassToCourse: vi.fn(), addStudentToCourse: vi.fn(), deleteStudentFromCourse: vi.fn(),
}));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() } }));

function student(overrides: Partial<CourseStudent>): CourseStudent {
  return {
    enrollment_id: 1, student_id: "c0000000-0000-4000-8000-000000000001", student_code: "6851071001",
    full_name: "Sinh Viên A", email: "6851071001@st.utc2.edu.vn", class_id: "CQ.68.CNTT", is_active: true,
    submitted_lessons: 0, accepted_problems: 0, total_lessons: 0, progress_percent: 0, submission_history: [],
    ...overrides,
  };
}

const active = student({});
const locked = student({
  enrollment_id: 2, student_id: "c0000000-0000-4000-8000-000000000002", student_code: "6851071002",
  full_name: "Sinh Viên B", email: "6851071002@st.utc2.edu.vn", is_active: false,
});

beforeEach(() => vi.resetAllMocks());

function renderTable(onChanged = vi.fn(), students: CourseStudent[] = [active, locked]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <CourseStudentsTable students={students} courseId="CS101-2026A" onChanged={onChanged} />
    </QueryClientProvider>,
  );
  return { user: userEvent.setup(), onChanged };
}

function row(name: string) {
  return within(screen.getByText(name).closest("tr")!);
}

it("marks only locked students with the 'Đã khoá' badge", () => {
  renderTable();
  expect(row("Sinh Viên B").getByText("Đã khoá")).toBeInTheDocument();
  expect(row("Sinh Viên A").queryByText("Đã khoá")).not.toBeInTheDocument();
});

it("locks a student of the course by UUID user_id and refreshes the roster", async () => {
  vi.mocked(adminApi.lockUser).mockResolvedValue({ user_id: active.student_id, full_name: active.full_name, email: active.email, role_id: 3, is_active: false });
  const { user, onChanged } = renderTable();
  await user.click(row("Sinh Viên A").getByRole("button", { name: "Khoá tài khoản Sinh Viên A" }));
  const dialog = within(await screen.findByRole("alertdialog"));
  expect(dialog.getByText(/6851071001/)).toBeInTheDocument();
  await user.click(dialog.getByRole("button", { name: "Xác nhận khoá" }));
  await waitFor(() => expect(adminApi.lockUser).toHaveBeenCalledWith(active.student_id));
  expect(toast.success).toHaveBeenCalledWith("Đã khoá tài khoản Sinh Viên A");
  await waitFor(() => expect(onChanged).toHaveBeenCalled());
});

it("shows the backend message when a teacher tries to unlock an account locked by an admin", async () => {
  vi.mocked(adminApi.unlockUser).mockRejectedValue(
    new ApiError({ status: 403, detail: "Tài khoản này chỉ Quản trị viên mới được mở khoá", code: "NOT_ALLOWED_TO_MANAGE_ACCOUNT" }),
  );
  const { user, onChanged } = renderTable();
  await user.click(row("Sinh Viên B").getByRole("button", { name: "Mở khoá tài khoản Sinh Viên B" }));
  await user.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xác nhận mở khoá" }));
  await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Tài khoản này chỉ Quản trị viên mới được mở khoá"));
  expect(toast.success).not.toHaveBeenCalled();
  await waitFor(() => expect(onChanged).toHaveBeenCalled());
});

it("edits a student's class through PATCH /users/{id} with only the changed field", async () => {
  vi.mocked(adminApi.updateUser).mockResolvedValue({ user_id: active.student_id, full_name: active.full_name, email: active.email, role_id: 3, class_id: "CQ.68.KTPM" });
  const { user, onChanged } = renderTable();
  await user.click(row("Sinh Viên A").getByRole("button", { name: "Sửa tài khoản Sinh Viên A" }));
  const dialog = within(await screen.findByRole("dialog"));
  const classInput = dialog.getByLabelText("Mã lớp hành chính");
  await user.clear(classInput);
  await user.type(classInput, "CQ.68.KTPM");
  await user.click(dialog.getByRole("button", { name: "Lưu thay đổi" }));
  await waitFor(() => expect(adminApi.updateUser).toHaveBeenCalledWith(active.student_id, { class_id: "CQ.68.KTPM" }));
  await waitFor(() => expect(onChanged).toHaveBeenCalled());
});

it("does not refetch when the teacher's own account was just locked (session already ended)", async () => {
  vi.mocked(adminApi.lockUser).mockRejectedValue(
    new ApiError({ status: 403, detail: "Tài khoản đã bị khoá", code: "ACCOUNT_LOCKED" }),
  );
  const { user, onChanged } = renderTable();
  await user.click(row("Sinh Viên A").getByRole("button", { name: "Khoá tài khoản Sinh Viên A" }));
  await user.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xác nhận khoá" }));
  await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Tài khoản đã bị khoá"));
  await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
  expect(onChanged).not.toHaveBeenCalled();
});

it("renames a student with no class and no student code without demanding them", async () => {
  // SV ghi danh khi chưa có lớp hành chính / MSSV (User.class_id, User.student_code nullable).
  const legacy = student({
    enrollment_id: 3, student_id: "c0000000-0000-4000-8000-000000000003", student_code: null,
    full_name: "Sinh Viên Cũ", email: "sv.cu@st.utc2.edu.vn", class_id: null,
  });
  vi.mocked(adminApi.updateUser).mockResolvedValue({ user_id: legacy.student_id, full_name: "Sinh Viên Mới", email: legacy.email, role_id: 3, class_id: null, student_code: null });
  const { user, onChanged } = renderTable(vi.fn(), [legacy]);
  await user.click(row("Sinh Viên Cũ").getByRole("button", { name: "Sửa tài khoản Sinh Viên Cũ" }));
  const dialog = within(await screen.findByRole("dialog"));
  const name = dialog.getByLabelText("Họ và tên");
  await user.clear(name);
  await user.type(name, "Sinh Viên Mới");
  await user.click(dialog.getByRole("button", { name: "Lưu thay đổi" }));
  await waitFor(() => expect(adminApi.updateUser).toHaveBeenCalledWith(legacy.student_id, { full_name: "Sinh Viên Mới" }));
  expect(dialog.queryByRole("alert")).not.toBeInTheDocument();
  await waitFor(() => expect(onChanged).toHaveBeenCalled());
});
