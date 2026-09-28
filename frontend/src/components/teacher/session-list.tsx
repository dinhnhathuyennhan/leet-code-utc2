"use client";

import { useMemo } from "react";
import { CalendarPlus } from "lucide-react";

import { EmptyState } from "@/components/shared/page-state";
import { SessionAlertBanner } from "@/components/teacher/SessionAlertBanner";
import { ClosedSessionCard, OpenSessionCard, UpcomingSessionCard } from "@/components/teacher/SessionCards";
import type { CourseSession } from "@/lib/types/course";

interface SessionListProps {
  sessions: CourseSession[];
  studentCount: number;
  onViewResults: () => void;
}

/** Danh sách buổi học, mới nhất trước; chọn kiểu thẻ theo trạng thái. */
export function SessionList({ sessions, studentCount, onViewResults }: SessionListProps) {
  const sorted = useMemo(() => [...sessions].sort((a, b) => b.order - a.order), [sessions]);
  const openSession = sorted.find((s) => s.status === "open");

  if (sorted.length === 0) {
    return <EmptyState icon={CalendarPlus} title="Chưa có buổi học nào" description="Nhấn Tạo buổi học để bắt đầu." />;
  }

  return (
    <div className="space-y-5">
      {openSession && <SessionAlertBanner session={openSession} studentCount={studentCount} />}
      {sorted.map((session) => {
        switch (session.status) {
          case "open":
            return <OpenSessionCard key={session.id} session={session} studentCount={studentCount} />;
          case "upcoming":
            return <UpcomingSessionCard key={session.id} session={session} />;
          case "closed":
            return <ClosedSessionCard key={session.id} session={session} studentCount={studentCount} onViewResults={onViewResults} />;
        }
      })}
    </div>
  );
}
