export interface Crumb {
  label: string;
  href?: string; // không có href = trang hiện tại
}

const SEGMENT_LABELS: Record<string, string> = {
  courses: "Lớp học phần",
  submissions: "Bài nộp",
  accounts: "Quản lý tài khoản",
  history: "Lịch sử nộp bài",
};

/**
 * Dựng breadcrumb từ pathname.
 * Segment động (vd: id lớp) lấy nhãn từ `dynamicLabel` — page đặt qua useBreadcrumbLabel().
 */
export function buildBreadcrumbs(pathname: string, dynamicLabel?: string | null): Crumb[] {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return [{ label: "Lớp học phần" }]; // trang chủ sinh viên
  if (pathname === "/teacher") return [{ label: "Tổng quan" }];

  const crumbs: Crumb[] = [];
  let href = "";
  segments.forEach((segment, index) => {
    href += `/${segment}`;
    if (segment === "teacher") return;
    const isLast = index === segments.length - 1;
    crumbs.push({
      label: SEGMENT_LABELS[segment] ?? dynamicLabel ?? "…",
      href: isLast ? undefined : href,
    });
  });
  return crumbs;
}
