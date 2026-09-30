import type { CourseStatus, SessionStatus } from "@/lib/types/course";

export type BadgeTone = "indigo" | "amber" | "green" | "blue" | "slate";

export const COURSE_STATUS: Record<CourseStatus, { label: string; tone: BadgeTone }> = {
  ongoing: { label: "Đang diễn ra", tone: "indigo" },
  upcoming: { label: "Sắp diễn ra", tone: "amber" },
  closed: { label: "Đã kết thúc", tone: "slate" },
};

export const SESSION_STATUS: Record<SessionStatus, { label: string; tone: BadgeTone }> = {
  upcoming: { label: "Sắp mở", tone: "amber" },
  open: { label: "Đang mở", tone: "green" },
  closed: { label: "Đã đóng", tone: "blue" },
};
