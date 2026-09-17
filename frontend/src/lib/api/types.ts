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

/** POST /auth/refresh only returns a fresh access token (no user object). */
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

export interface ImportStudentsError {
  row: number;
  email: string;
  reason: string;
}

export interface ImportStudentsResponse {
  created: CreateAccountResponse[];
  errors: ImportStudentsError[];
}

export interface ResetPasswordResponse {
  user_id: string;
  temporary_password: string;
}
