"use client";

import { useMemo, useState } from "react";
import { CalendarPlus } from "lucide-react";

import { EmptyState } from "@/components/shared/page-state";
import { ClosedSessionCard, OpenSessionCard, UpcomingSessionCard } from "@/components/teacher/session-cards";
import type { CourseSession } from "@/lib/types/course";
import { SessionAlertBanner } from "./session-alert-banner";

interface SessionListProps {
  sessions: CourseSession[];
  studentCount: number;
  courseId?: string | number;
  onViewResults: () => void;
}

/** Danh sách buổi học, mới nhất trước; chọn kiểu thẻ theo trạng thái. */
export function SessionList({ sessions, studentCount, courseId = "JAVA01", onViewResults }: SessionListProps) {
  const sorted = useMemo(() => [...sessions].sort((a, b) => b.order - a.order), [sessions]);
  const openSession = sorted.find((s) => s.status === "open");
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  if (sorted.length === 0) {
    return <EmptyState icon={CalendarPlus} title="Chưa có buổi học nào" description="Nhấn Tạo buổi học để bắt đầu." />;
  }

  return (
    <div className="space-y-5">
      {openSession && <SessionAlertBanner session={openSession} studentCount={studentCount} />}
      {sorted.map((session) => {
        switch (session.status) {
          case "open":
            return <OpenSessionCard key={session.id} session={session} courseId={courseId} selected={selectedSessionId === session.id} onSelect={() => setSelectedSessionId(session.id)} />;
          case "upcoming":
            return <UpcomingSessionCard key={session.id} session={session} courseId={courseId} selected={selectedSessionId === session.id} onSelect={() => setSelectedSessionId(session.id)} />;
          case "closed":
            return <ClosedSessionCard key={session.id} session={session} courseId={courseId} studentCount={studentCount} onViewResults={onViewResults} selected={selectedSessionId === session.id} onSelect={() => setSelectedSessionId(session.id)} />;
        }
      })}
    </div>
  );
}
