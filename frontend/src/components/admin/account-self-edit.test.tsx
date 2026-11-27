/**
 * Admin sửa chính tài khoản đang đăng nhập (PATCH /users/{user_id} với user_id của mình):
 * header, trang /login ("Tài khoản ... đang được sử dụng") đọc user từ AuthContext và
 * profile cache (sessionStorage), nên cả hai phải đổi theo — không chỉ dòng trong bảng.
 * Dùng AuthProvider thật (refresh qua MSW), chỉ mock các API quản lý tài khoản.
 */
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";

import { AccountManagement } from "./account-management";
import * as api from "@/lib/api/endpoints/admin";
import { AuthProvider, useAuth } from "@/context/auth-context";
import axiosInstance from "@/lib/axios";
import { setAccessToken } from "@/lib/auth/token-store";
import { server } from "@/test/mocks/server";
import type { AccountResponse } from "@/lib/api/types";

vi.mock("@/lib/api/endpoints/admin", () => ({
  listUsers: vi.fn(), createStudent: vi.fn(), createTeacher: vi.fn(),
  importStudents: vi.fn(), resetUserPassword: vi.fn(),
  lockUser: vi.fn(), unlockUser: vi.fn(), updateUser: vi.fn(),
}));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() } }));

const API = "http://localhost:8000";
const PROFILE_CACHE_KEY = "chamcode.profile";
const ADMIN_ID = "a0000000-0000-4000-8000-000000000001";

// Dòng của chính Admin đang đăng nhập; class_id/student_code NULL như mọi tài khoản không phải SV.
const self: AccountResponse = {
  user_id: ADMIN_ID, full_name: "Admin Chính", email: "admin@st.utc2.edu.vn", role_id: 1,
  student_code: null, class_id: null, is_active: true,
};
const teacher: AccountResponse = {
  user_id: "b0000000-0000-4000-8000-000000000001", full_name: "Giáo Viên A", email: "gva@st.utc2.edu.vn",
  role_id: 2, student_code: null, class_id: null, is_active: true,
};

function accessTokenFor(userId: string, role: number): string {
  const encode = (value: object) =>
    btoa(JSON.stringify(value)).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
  const now = Math.floor(Date.now() / 1000);
  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode({ sub: userId, role, tv: 1, type: "access", iat: now, exp: now + 3600 })}.sig`;
}

function CurrentUser() {
  const auth = useAuth();
  return <p data-testid="current-user">{auth.status === "authenticated" ? `${auth.user.full_name} <${auth.user.email}>` : auth.status}</p>;
}

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.listUsers).mockResolvedValue({ items: [self, teacher], total: 2, page: 1, page_size: 20 });
  sessionStorage.setItem(
    PROFILE_CACHE_KEY,
    JSON.stringify({ full_name: self.full_name, email: self.email, must_change_password: false }),
  );
  server.use(
    http.post(`${API}/auth/refresh-access-token`, () => HttpResponse.json({ access_token: accessTokenFor(ADMIN_ID, 1) })),
  );
});

afterEach(() => {
  setAccessToken(null);
  sessionStorage.clear();
});

async function renderSignedIn() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <CurrentUser />
        <AccountManagement />
      </AuthProvider>
    </QueryClientProvider>,
  );
  await waitFor(() => expect(screen.getByTestId("current-user")).toHaveTextContent("Admin Chính <admin@st.utc2.edu.vn>"));
  return userEvent.setup();
}

async function editRow(user: ReturnType<typeof userEvent.setup>, name: string, changes: { full_name?: string; email?: string }) {
  const row = within((await screen.findByText(name)).closest("tr")!);
  await user.click(row.getByRole("button", { name: `Sửa tài khoản ${name}` }));
  const dialog = within(await screen.findByRole("dialog"));
  if (changes.full_name !== undefined) {
    await user.clear(dialog.getByLabelText("Họ và tên"));
    await user.type(dialog.getByLabelText("Họ và tên"), changes.full_name);
  }
  if (changes.email !== undefined) {
    await user.clear(dialog.getByLabelText("Email UTC2"));
    await user.type(dialog.getByLabelText("Email UTC2"), changes.email);
  }
  await user.click(dialog.getByRole("button", { name: "Lưu thay đổi" }));
}

it("updates the signed-in admin in AuthContext and the profile cache after editing their own row", async () => {
  const updated = { ...self, full_name: "Admin Mới", email: "admin.new@st.utc2.edu.vn" };
  vi.mocked(api.updateUser).mockResolvedValue(updated);
  const user = await renderSignedIn();

  await editRow(user, "Admin Chính", { full_name: "Admin Mới", email: "admin.new@st.utc2.edu.vn" });

  await waitFor(() =>
    expect(api.updateUser).toHaveBeenCalledWith(ADMIN_ID, { full_name: "Admin Mới", email: "admin.new@st.utc2.edu.vn" }),
  );
  await waitFor(() => expect(screen.getByTestId("current-user")).toHaveTextContent("Admin Mới <admin.new@st.utc2.edu.vn>"));
  expect(JSON.parse(sessionStorage.getItem(PROFILE_CACHE_KEY)!)).toEqual({
    full_name: "Admin Mới",
    email: "admin.new@st.utc2.edu.vn",
    must_change_password: false,
  });
});

it("leaves the signed-in admin untouched when editing someone else", async () => {
  vi.mocked(api.updateUser).mockResolvedValue({ ...teacher, full_name: "Giáo Viên B", email: "gvb@st.utc2.edu.vn" });
  const user = await renderSignedIn();

  await editRow(user, "Giáo Viên A", { full_name: "Giáo Viên B", email: "gvb@st.utc2.edu.vn" });

  await waitFor(() => expect(api.updateUser).toHaveBeenCalledWith(teacher.user_id, { full_name: "Giáo Viên B", email: "gvb@st.utc2.edu.vn" }));
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  expect(screen.getByTestId("current-user")).toHaveTextContent("Admin Chính <admin@st.utc2.edu.vn>");
  expect(JSON.parse(sessionStorage.getItem(PROFILE_CACHE_KEY)!)).toMatchObject({ full_name: "Admin Chính", email: "admin@st.utc2.edu.vn" });
});

it("does not write the profile cache back when the session ended while the PATCH was in flight", async () => {
  let resolveUpdate!: (value: AccountResponse) => void;
  vi.mocked(api.updateUser).mockReturnValue(new Promise((resolve) => (resolveUpdate = resolve)));
  server.use(
    http.get(`${API}/users/me`, () =>
      HttpResponse.json({ error_code: "ACCOUNT_LOCKED", message: "Tài khoản đã bị khoá" }, { status: 403 }),
    ),
  );
  const user = await renderSignedIn();
  await editRow(user, "Admin Chính", { full_name: "Admin Mới" });
  await waitFor(() => expect(api.updateUser).toHaveBeenCalled());

  // Admin khác vừa khoá tài khoản này: một request khác nhận ACCOUNT_LOCKED → phiên kết thúc, cache bị dọn.
  await act(async () => {
    await axiosInstance.get("/users/me").catch(() => undefined);
  });
  expect(sessionStorage.getItem(PROFILE_CACHE_KEY)).toBeNull();

  await act(async () => {
    resolveUpdate({ ...self, full_name: "Admin Mới" });
  });

  expect(screen.getByTestId("current-user")).toHaveTextContent("unauthenticated");
  expect(sessionStorage.getItem(PROFILE_CACHE_KEY)).toBeNull();
});
