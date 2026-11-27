/** Role ids as defined by the backend (see backend/app/dependencies.py::Role). */
export const Role = {
  ADMIN: 1,
  TEACHER: 2,
  STUDENT: 3,
} as const;

export type Role = (typeof Role)[keyof typeof Role];

/** Mirrors backend/app/schemas/auth.py::UserResponse. */
export interface UserResponse {
  user_id: string;
  full_name: string;
  email: string;
  role_id: Role;
  must_change_password: boolean;
}

/** Mirrors backend/app/schemas/auth.py::LoginResponse. */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

/** POST /auth/refresh-access-token only returns a fresh access token (no user object). */
export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

/** Shared by POST /teachers and POST /students — see docs/api-design.md. */
export interface CreateAccountRequest {
  full_name: string;
  email: string;
}

export interface CreateAccountResponse {
  user_id: string;
  full_name: string;
  email: string;
  role_id: Role;
  temporary_password: string;
}

export interface ResetPasswordResponse {
  user_id: string;
  temporary_password: string;
}

export interface CreateTeacherRequest {
  full_name: string;
  email: string;
}

export interface CreateStudentRequest extends CreateTeacherRequest {
  student_code: string;
  class_id: string;
}

export interface AccountResponse {
  user_id: string;
  full_name: string;
  email: string;
  role_id: Role;
  student_code?: string | null;
  class_id?: string | null;
  /** `false` = tài khoản đang bị khoá. Thiếu field (dữ liệu cũ) coi như đang hoạt động. */
  is_active?: boolean;
}

/**
 * PATCH /users/{user_id} — mọi field đều tuỳ chọn, field không gửi thì giữ nguyên.
 * Giáo viên/Admin: `full_name`, `email`. Sinh viên: `full_name`, `student_code`, `class_id`
 * (email sinh viên tự đổi theo MSSV). Xem docs/api-design-auth.md.
 */
export interface UpdateUserRequest {
  full_name?: string;
  email?: string;
  student_code?: string;
  class_id?: string;
}

export interface ListUsersParams {
  role_id?: Role;
  class_id?: string;
  page?: number;
  page_size?: number;
}

export interface AccountListResponse {
  items: AccountResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface ImportStudentsCreatedRow {
  user_id: string;
  student_code: string;
  full_name: string;
  email: string;
  class_id: string;
  temporary_password: string;
}

export interface ImportStudentsSkippedRow {
  user_id: string;
  sheet: string;
  row: number;
  student_code: string;
  reason: string;
}

export interface ImportStudentsErrorRow {
  sheet: string;
  row: number;
  student_code: string | null;
  reason: string;
}

export interface ImportStudentsResponse {
  created: ImportStudentsCreatedRow[];
  skipped: ImportStudentsSkippedRow[];
  errors: ImportStudentsErrorRow[];
}
