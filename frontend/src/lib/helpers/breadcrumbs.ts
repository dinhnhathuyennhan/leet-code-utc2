import { DICTIONARY, type TranslationKey } from "@/lib/i18n";

export interface Crumb {
  label: string;
  href?: string; // không có href = trang hiện tại
}

/** Nhãn breadcrumb theo key — dịch qua `t()` của LocaleProvider. */
const SEGMENT_LABEL_KEYS: Record<string, TranslationKey> = {
  courses: "nav.courses",
  submissions: "nav.submissions",
  accounts: "nav.accounts",
  history: "nav.history",
  "problem-bank": "nav.problemBank",
  assignments: "nav.assignments",
};

type Translate = (key: TranslationKey) => string;

/** Nhãn tiếng Việt mặc định khi không có LocaleProvider. */
const DEFAULT_SEGMENT_LABELS: Partial<Record<TranslationKey, string>> = {
  "nav.courses": "Lớp học phần",
  "nav.submissions": "Bài nộp",
  "nav.accounts": "Quản lý tài khoản",
  "nav.history": "Lịch sử nộp bài",
  "nav.problemBank": "Ngân hàng đề",
  "nav.assignments": "Bài tập",
  "nav.overview": "Tổng quan",
  "teacher.tabs.sessions": "Buổi học",
};

/** Label động có thể là chuỗi thường hoặc key tra cứu bản dịch. */
export type DynamicLabel = string | TranslationKey | null | undefined;

/** Dịch label động nếu nó là key, ngược lại giữ nguyên chuỗi. */
function resolveLabel(label: DynamicLabel, t: Translate): string | undefined {
  if (label == null) return undefined;
  if (typeof label === "string" && label in DICTIONARY) {
    return t(label as TranslationKey);
  }
  return label;
}

/**
 * Dựng breadcrumb từ pathname.
 *
 * Segment động (vd: id lớp) lấy nhãn từ `dynamicLabel` — page đặt qua useBreadcrumbLabel().
 *
 * `translate` là hàm dịch của LocaleProvider; khi không truyền (vd: unit test
 * hoặc render ngoài provider) dùng nhãn tiếng Việt mặc định.
 */
export function buildBreadcrumbs(
  pathname: string,
  dynamicLabels?: {
    course: DynamicLabel;
    session: DynamicLabel;
    page?: DynamicLabel;
  },
  translate?: Translate,
): Crumb[] {
  const t: Translate = translate ?? ((key) => DEFAULT_SEGMENT_LABELS[key] ?? key);
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) return [{ label: t("nav.courses") }]; // trang chủ sinh viên
  if (pathname === "/teacher") return [{ label: t("nav.overview") }];

  if (segments[0] === "teacher" && segments[1] === "courses" && segments[2]) {
    const coursePath = `/teacher/courses/${segments[2]}`;
    const crumbs: Crumb[] = [
      { label: t("nav.courses"), href: "/teacher/courses" },
      {
        label: resolveLabel(dynamicLabels?.course, t) ?? segments[2],
        href: segments[4] ? coursePath : undefined,
      },
    ];
    if (segments[3] === "sessions" && segments[4]) {
      // SỬA: Khi có trang con như "Soạn bài tập", buổi học phải là link trung gian,
      // chỉ breadcrumb cuối cùng mới được đánh dấu trang hiện tại.
      crumbs.push({
        label: resolveLabel(dynamicLabels?.session, t) ?? t("teacher.tabs.sessions"),
        href: dynamicLabels?.page || segments[6] ? `${coursePath}/sessions/${segments[4]}` : undefined,
      });
      if (segments[5] === "problems" && segments[6]) {
        crumbs.push({ label: resolveLabel(dynamicLabels?.page, t) ?? t("nav.assignments") });
      } else if (dynamicLabels?.page) {
        crumbs.push({ label: resolveLabel(dynamicLabels.page, t) ?? "" });
      }
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
    const segmentKey = SEGMENT_LABEL_KEYS[segment];
    const isUnknown = !segmentKey;
    crumbs.push({
      // A dynamic label belongs only to the final dynamic route segment.
      // Applying it to every unknown segment caused `Buổi 2` to appear three times
      // on /teacher/courses/:courseId/sessions/:sessionId.
      label:
        (segmentKey ? t(segmentKey) : undefined) ??
        (isUnknown && visibleIndex === visibleSegments.length - 1
          ? resolveLabel(dynamicLabels?.session ?? dynamicLabels?.course, t)
          : undefined) ??
        "…",
      href: isLast ? undefined : href,
    });
    visibleIndex += 1;
  });
  return crumbs;
}
