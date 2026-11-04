"use client";

import { useQuery } from "@tanstack/react-query";
import { getAdminClasses, getAdminCourse, getAdminCourses, getAdminProfile } from "@/lib/api/endpoints/admin-management";
import { listUsers } from "@/lib/api/endpoints/admin";

export const adminKeys = {
  all: ["admin"] as const,
  courses: ["admin", "courses"] as const,
  course: (id: string) => ["admin", "course", id] as const,
  classes: ["admin", "classes"] as const,
  profile: ["admin", "profile"] as const,
  submissions: ["admin", "submissions"] as const,
  problems: ["admin", "problems"] as const,
};

export const useAdminCourses = () => useQuery({ queryKey: adminKeys.courses, queryFn: getAdminCourses });
export const useAdminCourse = (id: string) => useQuery({ queryKey: adminKeys.course(id), queryFn: () => getAdminCourse(id) });
export const useAdminClasses = () => useQuery({ queryKey: adminKeys.classes, queryFn: getAdminClasses });
export const useAdminProfile = () => useQuery({ queryKey: adminKeys.profile, queryFn: getAdminProfile });
export const useAdminAccountCount = (roleId?: 2 | 3) => useQuery({
  queryKey: ["accounts", "count", roleId ?? "all"],
  queryFn: async () => (await listUsers({ role_id: roleId, page: 1, page_size: 1 })).total,
});
