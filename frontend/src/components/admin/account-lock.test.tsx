import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { toast } from "sonner";

import { AccountManagement } from "./account-management";
import * as api from "@/lib/api/endpoints/admin";
import { ApiError } from "@/lib/api/error";
import { AuthContext } from "@/context/auth-context";
import type { AccountResponse } from "@/lib/api/types";

vi.mock("@/lib/api/endpoints/admin", () => ({
  listUsers: vi.fn(), createStudent: vi.fn(), createTeacher: vi.fn(),
  importStudents: vi.fn(), resetUserPassword: vi.fn(),
  lockUser: vi.fn(), unlockUser: vi.fn(), updateUser: vi.fn(),
}));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() } }));

const ADMIN_ID = "a0000000-0000-4000-8000-000000000001";
const self: AccountResponse = { user_id: ADMIN_ID, full_name: "Admin Chính", email: "admin@st.utc2.edu.vn", role_id: 1, is_active: true };
const otherAdmin: AccountResponse = { user_id: "a0000000-0000-4000-8000-000000000002", full_name: "Admin Khác", email: "admin2@st.utc2.edu.vn", role_id: 1, is_active: true };
const teacher: AccountResponse = { user_id: "b0000000-0000-4000-8000-000000000001", full_name: "Giáo Viên A", email: "gva@st.utc2.edu.vn", role_id: 2, is_active: true };
const lockedStudent: AccountResponse = {
  user_id: "c0000000-0000-4000-8000-000000000001", full_name: "Sinh Viên B", email: "6851071001@st.utc2.edu.vn",
  role_id: 3, student_code: "6851071001", class_id: "CQ.68.CNTT", is_active: false,
};
// Vai trò lạ (không thuộc 1/2/3): whitelist phải ẩn mọi thao tác quản lý.
const unknownRole = { user_id: "d0000000-0000-4000-8000-000000000001", full_name: "Vai Trò Lạ", email: "x@st.utc2.edu.vn", role_id: 4, is_active: true } as unknown as AccountResponse;
const ALL = [self, otherAdmin, teacher, lockedStudent, unknownRole];

const adminAuth = {
  status: "authenticated",
  user: { user_id: ADMIN_ID, role_id: 1, full_name: "Admin Chính", email: self.email, must_change_password: false },
} as never;

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.listUsers).mockImplementation(async (params = {}) => {
    const items = params.role_id ? ALL.filter((a) => a.role_id === params.role_id) : ALL;
    return { items, total: items.length, page: 1, page_size: 20 };
  });
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <AuthContext.Provider value={adminAuth}><AccountManagement /></AuthContext.Provider>
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

async function row(name: string) {
  return within((await screen.findByText(name)).closest("tr")!);
}

/** Số lần gọi danh sách chính (page_size 20), không tính 3 query đếm. */
function listCalls() {
  return vi.mocked(api.listUsers).mock.calls.filter(([params]) => params?.page_size === 20).length;
}

describe("Admin — trạng thái và quyền khoá", () => {
  it("shows the lock status of every account", async () => {
    renderPage();
    expect((await row("Sinh Viên B")).getByText("Đã khoá")).toBeInTheDocument();
    expect((await row("Giáo Viên A")).getByText("Hoạt động")).toBeInTheDocument();
  });

  it("offers lock only for teachers/students, never for itself or another admin", async () => {
    renderPage();
    expect((await row("Giáo Viên A")).getByRole("button", { name: "Khoá tài khoản Giáo Viên A" })).toBeInTheDocument();
    expect((await row("Sinh Viên B")).getByRole("button", { name: "Mở khoá tài khoản Sinh Viên B" })).toBeInTheDocument();
    expect((await row("Admin Chính")).queryByRole("button", { name: /khoá tài khoản/i })).not.toBeInTheDocument();
    expect((await row("Admin Khác")).queryByRole("button", { name: /khoá tài khoản/i })).not.toBeInTheDocument();
    // Admin sửa được chính mình, không sửa Admin khác.
    expect((await row("Admin Chính")).getByRole("button", { name: "Sửa tài khoản Admin Chính" })).toBeInTheDocument();
    expect((await row("Admin Khác")).queryByRole("button", { name: /Sửa tài khoản/ })).not.toBeInTheDocument();
  });

  it("hides edit and lock for an unknown role (whitelist, not blacklist)", async () => {
    renderPage();
    const unknown = await row("Vai Trò Lạ");
    expect(unknown.queryByRole("button", { name: /khoá tài khoản/i })).not.toBeInTheDocument();
    expect(unknown.queryByRole("button", { name: /Sửa tài khoản/ })).not.toBeInTheDocument();
  });
});

describe("Admin — khoá / mở khoá", () => {
  it("locks a teacher after confirmation, toasts and refetches the list", async () => {
    vi.mocked(api.lockUser).mockResolvedValue({ ...teacher, is_active: false });
    const user = renderPage();
    await user.click((await row("Giáo Viên A")).getByRole("button", { name: "Khoá tài khoản Giáo Viên A" }));
    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByText(/đăng xuất khỏi mọi thiết bị/)).toBeInTheDocument();
    const before = listCalls();
    await user.click(within(dialog).getByRole("button", { name: "Xác nhận khoá" }));

    await waitFor(() => expect(api.lockUser).toHaveBeenCalledWith(teacher.user_id));
    expect(api.unlockUser).not.toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalledWith("Đã khoá tài khoản Giáo Viên A");
    await waitFor(() => expect(listCalls()).toBeGreaterThan(before));
  });

  it("does nothing when the confirmation is cancelled", async () => {
    const user = renderPage();
    await user.click((await row("Giáo Viên A")).getByRole("button", { name: "Khoá tài khoản Giáo Viên A" }));
    await user.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Huỷ" }));
    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    expect(api.lockUser).not.toHaveBeenCalled();
  });

  it("unlocks a locked student", async () => {
    vi.mocked(api.unlockUser).mockResolvedValue({ ...lockedStudent, is_active: true });
    const user = renderPage();
    await user.click((await row("Sinh Viên B")).getByRole("button", { name: "Mở khoá tài khoản Sinh Viên B" }));
    await user.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xác nhận mở khoá" }));
    await waitFor(() => expect(api.unlockUser).toHaveBeenCalledWith(lockedStudent.user_id));
    expect(api.lockUser).not.toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalledWith("Đã mở khoá tài khoản Sinh Viên B");
  });

  it("shows the backend message as an error toast on NOT_ALLOWED_TO_MANAGE_ACCOUNT and still refetches", async () => {
    vi.mocked(api.lockUser).mockRejectedValue(
      new ApiError({ status: 403, detail: "Bạn không có quyền quản lý tài khoản này", code: "NOT_ALLOWED_TO_MANAGE_ACCOUNT" }),
    );
    const user = renderPage();
    await user.click((await row("Giáo Viên A")).getByRole("button", { name: "Khoá tài khoản Giáo Viên A" }));
    const before = listCalls();
    await user.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xác nhận khoá" }));
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Bạn không có quyền quản lý tài khoản này"));
    expect(toast.success).not.toHaveBeenCalled();
    await waitFor(() => expect(listCalls()).toBeGreaterThan(before));
    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
  });

  it("reports a 409 concurrent change with the backend message", async () => {
    vi.mocked(api.unlockUser).mockRejectedValue(
      new ApiError({ status: 409, detail: "Trạng thái tài khoản vừa thay đổi, vui lòng thử lại", code: "CONFLICT" }),
    );
    const user = renderPage();
    await user.click((await row("Sinh Viên B")).getByRole("button", { name: "Mở khoá tài khoản Sinh Viên B" }));
    await user.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xác nhận mở khoá" }));
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Trạng thái tài khoản vừa thay đổi, vui lòng thử lại"));
  });
});

describe("Admin — sửa tài khoản", () => {
  it("sends only the changed student fields (no email for students)", async () => {
    vi.mocked(api.updateUser).mockResolvedValue({ ...lockedStudent, student_code: "6851071002", email: "6851071002@st.utc2.edu.vn" });
    const user = renderPage();
    await user.click((await row("Sinh Viên B")).getByRole("button", { name: "Sửa tài khoản Sinh Viên B" }));
    const dialog = within(await screen.findByRole("dialog"));
    expect(dialog.queryByLabelText("Email UTC2")).not.toBeInTheDocument();
    const code = dialog.getByLabelText("Mã sinh viên (MSSV)");
    await user.clear(code);
    await user.type(code, "6851071002");
    await user.click(dialog.getByRole("button", { name: "Lưu thay đổi" }));
    await waitFor(() => expect(api.updateUser).toHaveBeenCalledWith(lockedStudent.user_id, { student_code: "6851071002" }));
    expect(toast.success).toHaveBeenCalled();
  });

  it("edits a teacher's email and blocks a non-UTC2 email before calling the API", async () => {
    vi.mocked(api.updateUser).mockResolvedValue({ ...teacher, email: "gvb@st.utc2.edu.vn" });
    const user = renderPage();
    await user.click((await row("Giáo Viên A")).getByRole("button", { name: "Sửa tài khoản Giáo Viên A" }));
    const dialog = within(await screen.findByRole("dialog"));
    expect(dialog.queryByLabelText("Mã sinh viên (MSSV)")).not.toBeInTheDocument();
    const email = dialog.getByLabelText("Email UTC2");
    await user.clear(email);
    await user.type(email, "gvb@gmail.com");
    await user.click(dialog.getByRole("button", { name: "Lưu thay đổi" }));
    expect(dialog.getByRole("alert")).toHaveTextContent("Email phải có đuôi @st.utc2.edu.vn.");
    expect(api.updateUser).not.toHaveBeenCalled();

    await user.clear(email);
    await user.type(email, "gvb@st.utc2.edu.vn");
    await user.click(dialog.getByRole("button", { name: "Lưu thay đổi" }));
    await waitFor(() => expect(api.updateUser).toHaveBeenCalledWith(teacher.user_id, { email: "gvb@st.utc2.edu.vn" }));
  });

  it("does not call the API when nothing changed", async () => {
    const user = renderPage();
    await user.click((await row("Giáo Viên A")).getByRole("button", { name: "Sửa tài khoản Giáo Viên A" }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Lưu thay đổi" }));
    expect(api.updateUser).not.toHaveBeenCalled();
    expect(toast.info).toHaveBeenCalledWith("Không có thay đổi nào.");
  });

  it("keeps the dialog open and shows FIELD_NOT_EDITABLE from the backend", async () => {
    vi.mocked(api.updateUser).mockRejectedValue(
      new ApiError({ status: 422, detail: "Email sinh viên được tạo tự động theo MSSV, không thể sửa trực tiếp", code: "FIELD_NOT_EDITABLE" }),
    );
    const user = renderPage();
    await user.click((await row("Sinh Viên B")).getByRole("button", { name: "Sửa tài khoản Sinh Viên B" }));
    const dialog = within(await screen.findByRole("dialog"));
    const name = dialog.getByLabelText("Họ và tên");
    await user.clear(name);
    await user.type(name, "Sinh Viên  Bê");
    await user.click(dialog.getByRole("button", { name: "Lưu thay đổi" }));
    await waitFor(() => expect(dialog.getByRole("alert")).toHaveTextContent("không thể sửa trực tiếp"));
    // Khoảng trắng thừa được gộp như backend.
    expect(api.updateUser).toHaveBeenCalledWith(lockedStudent.user_id, { full_name: "Sinh Viên Bê" });
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });
});
