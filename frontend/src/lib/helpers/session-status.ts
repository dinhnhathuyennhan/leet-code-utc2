import type { SessionStatus } from "@/lib/types/course";
export type { SessionStatus };

const VN_OFFSET = "+07:00";

/** Lesson theo tài liệu: mở 00:00 ngày start_date, hết hạn 23:59:59.999 ngày end_date (giờ VN). */
function parseEdge(value: string, edge: "start" | "end") {
  if (value.length === 10) {
    const time = edge === "start" ? "00:00:00.000" : "23:59:59.999";
    return new Date(`${value}T${time}${VN_OFFSET}`);
  }
  return new Date(value);
}

export function getSessionStatus(start: string, end: string, now = new Date()): SessionStatus {
  if (now < parseEdge(start, "start")) return "upcoming";
  if (now > parseEdge(end, "end")) return "closed";
  return "open";
}