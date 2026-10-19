import { StudentDashboardPage } from "@/components/student/student-dashboard-page";

// Trang "Tổng quan" của sinh viên — trang chủ sau khi login.
// Layout (AppShell + Sidebar UTC2) được wrap bởi `app/(dashboard)/student/layout.tsx`.
export default function Page() {
  return <StudentDashboardPage />;
}
