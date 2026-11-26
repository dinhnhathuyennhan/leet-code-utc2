import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type {
  AccountResponse,
  AccountListResponse,
  CreateStudentRequest,
  CreateTeacherRequest,
  ImportStudentsResponse,
  ListUsersParams,
  ResetPasswordResponse,
  UpdateUserRequest,
} from "@/lib/api/types";

const userUrl = (userId: string) => `/users/${encodeURIComponent(userId)}`;

export async function listUsers(params: ListUsersParams = {}): Promise<AccountListResponse> {
  try {
    const response = await axiosInstance.get<AccountListResponse>("/users", { params });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function createTeacher(data: CreateTeacherRequest): Promise<AccountResponse> {
  try {
    const response = await axiosInstance.post<AccountResponse>("/teachers", data);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function createStudent(data: CreateStudentRequest): Promise<AccountResponse> {
  try {
    const response = await axiosInstance.post<AccountResponse>("/students", data);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function importStudents(file: File): Promise<ImportStudentsResponse> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await axiosInstance.post<ImportStudentsResponse>("/students/import", formData, {
      // Override the instance's JSON default; otherwise Axios serializes FormData as { file: {} }.
      // In browsers Axios removes this header before sending so the browser adds the multipart boundary.
      headers: { "Content-Type": "multipart/form-data" },
      // Hashing hundreds of passwords can exceed the default 10-second API timeout.
      timeout: 120_000,
    });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function resetUserPassword(userId: string): Promise<ResetPasswordResponse> {
  try {
    const response = await axiosInstance.post<ResetPasswordResponse>(`${userUrl(userId)}/reset-password`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** PATCH /users/{user_id} — sửa thông tin tài khoản (422 `FIELD_NOT_EDITABLE` nếu gửi field không hợp với vai trò). */
export async function updateUser(userId: string, data: UpdateUserRequest): Promise<AccountResponse> {
  try {
    const response = await axiosInstance.patch<AccountResponse>(userUrl(userId), data);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** POST /users/{user_id}/lock — idempotent; khoá thì đăng xuất tài khoản khỏi mọi thiết bị. */
export async function lockUser(userId: string): Promise<AccountResponse> {
  try {
    const response = await axiosInstance.post<AccountResponse>(`${userUrl(userId)}/lock`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** POST /users/{user_id}/unlock — idempotent; người dùng phải đăng nhập lại sau khi mở khoá. */
export async function unlockUser(userId: string): Promise<AccountResponse> {
  try {
    const response = await axiosInstance.post<AccountResponse>(`${userUrl(userId)}/unlock`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}
