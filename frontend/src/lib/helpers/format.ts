// format.ts – các hàm format chung dùng trong UI.
// formatDeadline / formatDate / formatUpdatedAt đã chuyển sang datetime.ts
// dùng Intl.DateTimeFormat với timeZone VN để hiển thị đúng mọi múi giờ.
export { formatDeadline, formatDate, formatUpdatedAt } from "./datetime";

/** → "HK1 (2024 - 2025) · Nhóm 02" */
export function formatTerm(c: { semester: number; academic_year: string; group: number }): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `HK${c.semester} (${c.academic_year.replace("-", " - ")}) · Nhóm ${pad(c.group)}`;
}

/** Chữ cái đầu của tên gọi (từ cuối cùng): "Nguyễn Văn An" → "A" */
export function getInitial(fullName: string): string {
  return fullName.trim().split(/\s+/).pop()?.charAt(0).toUpperCase() ?? "?";
}
