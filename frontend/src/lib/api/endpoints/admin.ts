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
} from "@/lib/api/types";

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
    const response = await axiosInstance.post<ResetPasswordResponse>(`/users/${encodeURIComponent(userId)}/reset-password`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}
