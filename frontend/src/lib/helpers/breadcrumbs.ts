export interface Crumb {
  label: string;
  href?: string; // không có href = trang hiện tại
}

const SEGMENT_LABELS: Record<string, string> = {
  courses: "Lớp học phần",
  submissions: "Bài nộp",
  accounts: "Quản lý tài khoản",
  history: "Lịch sử nộp bài",
  "problem-bank": "Ngân hàng đề",
};

/**
 * Dựng breadcrumb từ pathname.
 * Segment động (vd: id lớp) lấy nhãn từ `dynamicLabel` — page đặt qua useBreadcrumbLabel().
 */
export function buildBreadcrumbs(pathname: string, dynamicLabels?: { course: string | null; session: string | null; page?: string | null }): Crumb[] {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return [{ label: "Lớp học phần" }]; // trang chủ sinh viên
  if (pathname === "/teacher") return [{ label: "Tổng quan" }];

  if (segments[0] === "admin") {
    const labels: Record<string, string> = {
      dashboard: "Tổng quan", courses: "Lớp học phần", classes: "Lớp hành chính",
      accounts: "Quản lý tài khoản", submissions: "Bài nộp", settings: "Cấu hình",
      "problem-bank": "Ngân hàng đề", import: "Nhập từ Excel",
    };
    if (segments[1] === "courses" && segments[2]) {
      const coursePath = `/admin/courses/${segments[2]}`;
      const result: Crumb[] = [
        { label: "Lớp học phần", href: "/admin/courses" },
        { label: dynamicLabels?.course ?? decodeURIComponent(segments[2]), href: segments[4] ? coursePath : undefined },
      ];
      if (segments[3] === "sessions" && segments[4]) {
        result.push({ label: dynamicLabels?.session ?? `Buổi #${segments[4]}`, href: segments[6] ? `${coursePath}/sessions/${segments[4]}` : undefined });
        if (segments[5] === "problems" && segments[6]) result.push({ label: dynamicLabels?.page ?? "Nội dung bài tập" });
      }
      return result;
    }
    return segments.slice(1).map((segment, index) => ({
      label: labels[segment] ?? dynamicLabels?.page ?? `#${decodeURIComponent(segment)}`,
      href: index === segments.length - 2 ? undefined : `/admin/${segments.slice(1, index + 2).join("/")}`,
    }));
  }

  if (segments[0] === "teacher" && segments[1] === "courses" && segments[2]) {
    const coursePath = `/teacher/courses/${segments[2]}`;
    const crumbs: Crumb[] = [
      { label: "Lớp học phần", href: "/teacher/courses" },
      { label: dynamicLabels?.course ?? segments[2], href: segments[4] ? coursePath : undefined },
    ];
    if (segments[3] === "sessions" && segments[4]) {
      // SỬA: Khi có trang con như "Soạn bài tập", buổi học phải là link trung gian,
      // chỉ breadcrumb cuối cùng mới được đánh dấu trang hiện tại.
      crumbs.push({ label: dynamicLabels?.session ?? "Buổi học", href: dynamicLabels?.page || segments[6] ? `${coursePath}/sessions/${segments[4]}` : undefined });
      if (segments[5] === "problems" && segments[6]) crumbs.push({ label: dynamicLabels?.page ?? "Chi tiết bài tập" });
      else if (dynamicLabels?.page) crumbs.push({ label: dynamicLabels.page });
    }
    return crumbs;
  }

  const crumbs: Crumb[] = [];
  let href = "";
  const visibleSegments = segments.filter((segment) => segment !== "teacher" && segment !== "student");
  let visibleIndex = 0;
  segments.forEach((segment, index) => {
    href += `/${segment}`;
    if (segment === "teacher" || segment === "student") return;
    const isLast = index === segments.length - 1;
    const isUnknown = !(segment in SEGMENT_LABELS);
    crumbs.push({
      // A dynamic label belongs only to the final dynamic route segment.
      // Applying it to every unknown segment caused `Buổi 2` to appear three times
      // on /teacher/courses/:courseId/sessions/:sessionId.
      label: SEGMENT_LABELS[segment] ?? (isUnknown && visibleIndex === visibleSegments.length - 1 ? dynamicLabels?.session ?? dynamicLabels?.course : undefined) ?? "…",
      href: isLast ? undefined : href,
    });
    visibleIndex += 1;
  });
  return crumbs;
}
