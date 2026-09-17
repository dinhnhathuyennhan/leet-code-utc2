import { apiFetch } from "@/lib/api/client";
import type {
  CreateAccountRequest,
  CreateAccountResponse,
  ImportStudentsResponse,
  ResetPasswordResponse,
} from "@/lib/api/types";

/** POST /teachers — Admin only. Not implemented server-side yet. */
export function createTeacher(data: CreateAccountRequest): Promise<CreateAccountResponse> {
  return apiFetch<CreateAccountResponse>("/teachers", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** POST /students — Admin/Teacher. Implemented server-side (see backend/app/routers/student.py). */
export function createStudent(data: CreateAccountRequest): Promise<CreateAccountResponse> {
  return apiFetch<CreateAccountResponse>("/students", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** POST /students/import — multipart .xlsx upload. Not implemented server-side yet. */
export function importStudents(file: File): Promise<ImportStudentsResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<ImportStudentsResponse>("/students/import", {
    method: "POST",
    body: formData,
  });
}

/** POST /users/{user_id}/reset-password — Admin/Teacher. Not implemented server-side yet. */
export function resetPassword(userId: string): Promise<ResetPasswordResponse> {
  return apiFetch<ResetPasswordResponse>(
    `/users/${encodeURIComponent(userId)}/reset-password`,
    { method: "POST" },
  );
}
