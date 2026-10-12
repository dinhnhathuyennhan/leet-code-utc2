import {
  FileCheck2,
  GraduationCap,
  History,
  LayoutDashboard,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** true → chỉ active khi pathname trùng khớp hoàn toàn (vd: trang chủ). */
  exact?: boolean;
  /** Các prefix khác cũng làm mục này sáng lên. */
  alsoMatch?: string[];
}

export const TEACHER_NAV: NavItem[] = [
  { label: "Tổng quan", href: "/teacher", icon: LayoutDashboard, exact: true },
  { label: "Lớp học phần", href: "/teacher/courses", icon: GraduationCap },
  { label: "Bài nộp", href: "/teacher/submissions", icon: FileCheck2 },
  { label: "Quản lý tài khoản", href: "/teacher/accounts", icon: ShieldCheck },
];

export const STUDENT_NAV: NavItem[] = [
  // SV: "Lớp học phần" là trang chủ (/) và cũng match các trang chi tiết lớp (/student/classes/[id]).
  { label: "Lớp học phần", href: "/", icon: GraduationCap, exact: true, alsoMatch: ["/student/classes"] },
  { label: "Lịch sử nộp bài", href: "/student/history", icon: History },
];
