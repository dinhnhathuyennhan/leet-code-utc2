// format.ts – các hàm format chung dùng trong UI.
// formatDeadline / formatDate / formatUpdatedAt đã chuyển sang datetime.ts
// dùng Intl.DateTimeFormat với timeZone VN để hiển thị đúng mọi múi giờ.
export { formatDeadline, formatDate, formatUpdatedAt } from "./datetime";

import type { Locale } from "@/lib/i18n";

/**
 * → "HK1 (2024 - 2025) · Nhóm 02" (vi) / "Semester 1 (2024 - 2025) · Group 02" (en)
 *
 * `locale` quyết định cách viết tắt học kỳ và "Nhóm".
 */
export function formatTerm(
  c: { semester: number; academic_year: string; group: number },
  locale: Locale = "vi",
): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  const year = c.academic_year.replace("-", " - ");
  if (locale === "en") {
    return `Semester ${c.semester} (${year}) · Group ${pad(c.group)}`;
  }
  return `HK${c.semester} (${year}) · Nhóm ${pad(c.group)}`;
}

/** Chữ cái đầu của tên gọi (từ cuối cùng): "Nguyễn Văn An" → "A" */
export function getInitial(fullName: string): string {
  return fullName.trim().split(/\s+/).pop()?.charAt(0).toUpperCase() ?? "?";
}
