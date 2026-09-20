import type { UserResponse } from "@/lib/api/types";

const HOME_BY_ROLE: Record<number, string> = {
  1: "/admin-dashboard",
  2: "/teacher-dashboard",
  3: "/student-dashboard",
};

export function getHomePath(user: UserResponse): string {
  if (user.must_change_password) {
    return "/change-password";
  }
  return HOME_BY_ROLE[user.role_id] ?? "/";
}