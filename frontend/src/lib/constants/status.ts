import type { CourseStatus, SessionStatus } from "@/lib/types/course";
import type { TranslationKey } from "@/lib/i18n";

export type BadgeTone = "indigo" | "amber" | "green" | "blue" | "slate";

export const COURSE_STATUS: Record<CourseStatus, { label: string; labelKey: TranslationKey; tone: BadgeTone }> = {
  ongoing: { label: "Đang diễn ra", labelKey: "status.ongoing", tone: "indigo" },
  upcoming: { label: "Sắp diễn ra", labelKey: "status.upcoming", tone: "amber" },
  closed: { label: "Đã kết thúc", labelKey: "status.closed", tone: "slate" },
};

export const SESSION_STATUS: Record<SessionStatus, { label: string; labelKey: TranslationKey; tone: BadgeTone }> = {
  upcoming: { label: "Sắp mở", labelKey: "status.sessionUpcoming", tone: "amber" },
  open: { label: "Đang mở", labelKey: "status.sessionOpen", tone: "green" },
  closed: { label: "Đã đóng", labelKey: "status.sessionClosed", tone: "blue" },
};
