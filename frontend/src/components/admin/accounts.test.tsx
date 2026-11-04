import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import { AccountManagement } from "./account-management";
import { StudentImport } from "./student-import";
import * as api from "@/lib/api/endpoints/admin";

vi.mock("@/lib/api/endpoints/admin", () => ({
  listUsers: vi.fn(), createStudent: vi.fn(), createTeacher: vi.fn(),
  importStudents: vi.fn(), resetUserPassword: vi.fn(),
}));

const uuid = "d7675c0e-924f-4a9f-bf92-1cbe3fc925a8";

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.listUsers).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 });
});

async function openForm() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><AccountManagement /></QueryClientProvider>);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Cấp tài khoản" }));
  return { user, dialog: within(screen.getByRole("dialog")) };
}

it("creates a student with student_code and shows MSSV rather than UUID as the password", async () => {
  vi.mocked(api.createStudent).mockResolvedValue({
    user_id: uuid, student_code: "6851071001", full_name: "Student", email: "student@st.utc2.edu.vn", role_id: 3,
  });
  const { user, dialog } = await openForm();
  await user.type(dialog.getByLabelText("Mã sinh viên (MSSV)"), "6851071001");
  await user.type(dialog.getByLabelText("Họ và tên"), "Student");
  await user.type(dialog.getByLabelText("Email UTC2"), "student@st.utc2.edu.vn");
  await user.type(dialog.getByLabelText("Mã lớp hành chính"), "CQ.68.CNTT");
  await user.click(dialog.getByRole("button", { name: "Cấp phát tài khoản" }));

  expect(await dialog.findByText("6851071001", { selector: "code" })).toBeInTheDocument();
  expect(api.createStudent).toHaveBeenCalledWith({
    student_code: "6851071001", full_name: "Student", email: "student@st.utc2.edu.vn", class_id: "CQ.68.CNTT",
  });
  expect(api.createTeacher).not.toHaveBeenCalled();
});

it("creates a teacher without MSSV or birthday and shows email as the password", async () => {
  const email = "teacher@ST.UTC2.EDU.VN";
  vi.mocked(api.createTeacher).mockResolvedValue({ user_id: uuid, full_name: "Teacher", email, role_id: 2 });
  const { user, dialog } = await openForm();
  await user.click(dialog.getByRole("button", { name: "Giảng viên" }));
  expect(dialog.queryByLabelText("Mã sinh viên (MSSV)")).not.toBeInTheDocument();
  expect(dialog.queryByLabelText("Ngày sinh")).not.toBeInTheDocument();
  await user.type(dialog.getByLabelText("Họ và tên"), "Teacher");
  await user.type(dialog.getByLabelText("Email UTC2"), email);
  await user.click(dialog.getByRole("button", { name: "Cấp phát tài khoản" }));

  expect(await dialog.findByText(email, { selector: "code" })).toBeInTheDocument();
  expect(api.createTeacher).toHaveBeenCalledWith({ full_name: "Teacher", email });
  expect(api.createStudent).not.toHaveBeenCalled();
});

it("blocks an invalid student code before calling the API", async () => {
  const { user, dialog } = await openForm();
  await user.type(dialog.getByLabelText("Mã sinh viên (MSSV)"), "123");
  await user.type(dialog.getByLabelText("Họ và tên"), "Student");
  const form = dialog.getByLabelText("Họ và tên").closest("form")!;
  fireEvent.submit(form);
  expect(api.createStudent).not.toHaveBeenCalled();
});

it("displays student_code for created, skipped and invalid import rows", async () => {
  vi.mocked(api.importStudents).mockResolvedValue({
    created: [{ user_id: uuid, student_code: "6851071001", full_name: "Student", email: "student@st.utc2.edu.vn", class_id: "CQ.68.CNTT", temporary_password: "6851071001" }],
    skipped: [{ user_id: "e7675c0e-924f-4a9f-bf92-1cbe3fc925a8", sheet: "Sheet1", row: 12, student_code: "6851071002", reason: "Already exists" }],
    errors: [{ sheet: "Sheet1", row: 13, student_code: "invalid-code", reason: "Invalid code" }],
  });
  render(<StudentImport />);
  const user = userEvent.setup();
  await user.upload(screen.getByLabelText("Chọn file Excel danh sách sinh viên"), new File(["data"], "students.xlsx"));
  await user.click(screen.getByRole("button", { name: "Tải lên và tạo tài khoản" }));
  expect(await screen.findByText("6851071001", { selector: "td" })).toBeInTheDocument();
  expect(screen.getByText("6851071002", { selector: "td" })).toBeInTheDocument();
  expect(screen.getByText("invalid-code", { selector: "td" })).toBeInTheDocument();
});
