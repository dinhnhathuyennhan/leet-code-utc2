"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { CalendarPlus } from "lucide-react";

import { EmptyState } from "@/components/shared/page-state";
import { ClosedSessionCard, OpenSessionCard, UpcomingSessionCard } from "@/components/teacher/session-cards";
import type { CourseSession } from "@/lib/types/course";
import { SessionAlertBanner } from "./session-alert-banner";

interface SessionListProps {
  sessions: CourseSession[];
  studentCount: number;
  courseId?: string | number;
}

/** Danh sách buổi học, mới nhất trước; chọn kiểu thẻ theo trạng thái. */
export function SessionList({ sessions, studentCount, courseId = "JAVA01" }: SessionListProps) {
  const router = useRouter();
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
            return <OpenSessionCard key={session.id} session={session} courseId={courseId} studentCount={studentCount} onSelect={() => router.push(`/teacher/courses/${courseId}/sessions/${session.id}`)} />;
          case "upcoming":
            return <UpcomingSessionCard key={session.id} session={session} courseId={courseId} onSelect={() => router.push(`/teacher/courses/${courseId}/sessions/${session.id}`)} />;
          case "closed":
            return <ClosedSessionCard key={session.id} session={session} courseId={courseId} studentCount={studentCount} onSelect={() => router.push(`/teacher/courses/${courseId}/sessions/${session.id}`)} />;
        }
      })}
    </div>
  );
}
