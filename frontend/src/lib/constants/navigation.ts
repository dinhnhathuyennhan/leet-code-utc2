import {
  FileCheck2,
  BookOpenCheck,
  BookOpen,
  GraduationCap,
  History,
  LayoutDashboard,
  Settings,
  Users,
  type LucideIcon,
} from "lucide-react";

import type { TranslationKey } from "@/lib/i18n";

export interface NavItem {
  /** Nhãn hiển thị khi chưa có i18n context (fallback tiếng Việt). */
  label: string;
  /** Key tra cứu bản dịch — nếu có, sẽ được ưu tiên hơn `label`. */
  labelKey?: TranslationKey;
  href: string;
  icon: LucideIcon;
  /** true → chỉ active khi pathname trùng khớp hoàn toàn (vd: trang chủ). */
  exact?: boolean;
  /** Các prefix khác cũng làm mục này sáng lên. */
  alsoMatch?: string[];
}

export const TEACHER_NAV: NavItem[] = [
  {
    label: "Tổng quan",
    labelKey: "nav.overview",
    href: "/teacher",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    label: "Lớp học phần",
    labelKey: "nav.courses",
    href: "/teacher/courses",
    icon: GraduationCap,
  },
  {
    label: "Bài nộp",
    labelKey: "nav.submissions",
    href: "/teacher/submissions",
    icon: FileCheck2,
  },
  {
    label: "Ngân hàng đề",
    labelKey: "nav.problemBank",
    href: "/teacher/problem-bank",
    icon: BookOpenCheck,
  },
  // { label: "Quản lý tài khoản", labelKey: "nav.accounts", href: "/teacher/accounts", icon: ShieldCheck },
];

export const STUDENT_NAV: NavItem[] = [
  // SV: "Tổng quan" = trang chủ /student/dashboard
  //     "Lớp học phần" = danh sách + chi tiết lớp
  //     "Bài tập" = danh sách bài tập gom từ mọi lớp + chi tiết bài tập
  {
    label: "Tổng quan",
    labelKey: "nav.overview",
    href: "/student/dashboard",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    label: "Lớp học phần",
    labelKey: "nav.courses",
    href: "/student/classes",
    icon: GraduationCap,
  },
  {
    label: "Bài tập",
    labelKey: "nav.assignments",
    href: "/student/assignments",
    icon: BookOpenCheck,
  },
  {
    label: "Lịch sử nộp bài",
    labelKey: "nav.history",
    href: "/student/history",
    icon: History,
  },
];

export const ADMIN_NAV: NavItem[] = [
  {
    label: "Tổng quan",
    labelKey: "nav.overview",
    href: "/admin/dashboard",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    label: "Lớp học phần",
    labelKey: "nav.courses",
    href: "/admin/courses",
    icon: GraduationCap,
  },
  { label: "Lớp hành chính", href: "/admin/classes", icon: BookOpen },
  {
    label: "Quản lý tài khoản",
    labelKey: "nav.accounts",
    href: "/admin/accounts",
    icon: Users,
  },
  {
    label: "Bài nộp",
    labelKey: "nav.submissions",
    href: "/admin/submissions",
    icon: FileCheck2,
  },
  { label: "Ngân hàng đề", href: "/admin/problem-bank", icon: BookOpenCheck },
  {
    label: "Cấu hình",
    labelKey: "nav.settings",
    href: "/admin/settings",
    icon: Settings,
  },
];
