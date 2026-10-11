import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type {
  AccountResponse,
  CreateStudentRequest,
  CreateTeacherRequest,
  ImportStudentsResponse,
  ResetPasswordResponse,
} from "@/lib/api/types";

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
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function resetUserPassword(userId: string): Promise<ResetPasswordResponse> {
  try {
    const response = await axiosInstance.post<ResetPasswordResponse>(`/users/${userId}/reset-password`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}
