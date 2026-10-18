export interface Crumb {
  label: string;
  href?: string; // không có href = trang hiện tại
}

const SEGMENT_LABELS: Record<string, string> = {
  classes: "Lớp học phần",
  courses: "Lớp học phần",
  submissions: "Bài nộp",
  accounts: "Quản lý tài khoản",
  history: "Lịch sử nộp bài", // segment "history" bên trong /student/history
};

/**
 * Decode URI an toàn — tránh throw khi segment chứa ký tự % không hợp lệ
 * (vd: input thô từ user). Trả về nguyên bản nếu decode fail.
 */
function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

/**
 * Dựng breadcrumb từ pathname.
 *
 * Ưu tiên hiển thị theo thứ tự:
 *   1. SEGMENT_LABELS[segment] — nhãn cố định cho segment tĩnh (vd: "classes" → "Lớp học phần").
 *   2. dynamicLabel           — page set qua useBreadcrumbLabel() (vd: tên/mã lớp từ API).
 *   3. segment gốc            — fallback CUỐI CÙNG: hiển thị chính segment (vd: "CS101", "CS#202").
 *      Đảm bảo breadcrumb KHÔNG BAO GIỜ trống/kẹt "…"/"—" dù dynamicLabel chưa sẵn sàng.
 */
export function buildBreadcrumbs(pathname: string, dynamicLabel?: string | null): Crumb[] {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return [{ label: "Lớp học phần" }]; // trang chủ sinh viên
  if (pathname === "/teacher") return [{ label: "Tổng quan" }];
  if (pathname === "/student/dashboard") return [{ label: "Tổng quan" }];

  const crumbs: Crumb[] = [];
  let href = "";
  segments.forEach((segment, index) => {
    href += `/${segment}`;
    if (segment === "teacher" || segment === "student") return;
    const isLast = index === segments.length - 1;
    // Fallback chain: SEGMENT_LABELS → dynamicLabel → segment gốc (đã decode).
    // next/navigation usePathname() KHÔNG tự decode %23 → cần decodeURIComponent để hiển thị "CS#202" thay vì "CS%23202".
    const label =
      SEGMENT_LABELS[segment] ??
      (dynamicLabel && dynamicLabel.trim() !== "" ? dynamicLabel : null) ??
      safeDecode(segment);
    crumbs.push({
      label,
      href: isLast ? undefined : href,
    });
  });
  return crumbs;
}
