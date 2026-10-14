import {
  FileCheck2,
  BookOpenCheck,
  GraduationCap,
  History,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  Users,
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
  { label: "Ngân hàng đề", href: "/teacher/problem-bank", icon: BookOpenCheck },
  { label: "Quản lý tài khoản", href: "/teacher/accounts", icon: ShieldCheck },
];

export const STUDENT_NAV: NavItem[] = [
  { label: "Lớp học phần", href: "/", icon: GraduationCap, exact: true, alsoMatch: ["/courses"] },
  { label: "Lịch sử nộp bài", href: "/history", icon: History },
];

export const ADMIN_NAV: NavItem[] = [
  { label: "Tổng quan", href: "/admin/dashboard", icon: LayoutDashboard, exact: true },
  { label: "Lớp học phần", href: "/admin/courses", icon: GraduationCap },
  { label: "Quản lý tài khoản", href: "/admin/accounts", icon: Users },
  { label: "Bài nộp", href: "/admin/submissions", icon: FileCheck2 },
  { label: "Cấu hình", href: "/admin/settings", icon: Settings },
];
