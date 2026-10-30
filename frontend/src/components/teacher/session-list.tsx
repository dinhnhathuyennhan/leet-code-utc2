"use client";

import { useMemo, useState, type DragEvent } from "react";
import { useRouter } from "next/navigation";
import { CalendarPlus, GripVertical, Save } from "lucide-react";

import { EmptyState } from "@/components/shared/page-state";
import { ClosedSessionCard, OpenSessionCard, UpcomingSessionCard } from "@/components/teacher/session-cards";
import type { CourseSession } from "@/lib/types/course";
import { SessionAlertBanner } from "./session-alert-banner";
import { Button } from "@/components/ui/button";
import { reorderLessons } from "@/lib/api/endpoints/courses";
import { toast } from "sonner";

interface SessionListProps {
  sessions: CourseSession[];
  studentCount: number;
  courseId?: string | number;
  onChanged?: () => void;
}

/** Danh sách buổi học, mới nhất trước; chọn kiểu thẻ theo trạng thái. */
export function SessionList({ sessions, studentCount, courseId = "JAVA01", onChanged }: SessionListProps) {
  const router = useRouter();
  const [draft, setDraft] = useState(() => [...sessions].sort((a, b) => a.order - b.order));
  const [draggedId, setDraggedId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const sorted = useMemo(() => [...draft].sort((a, b) => b.order - a.order), [draft]);
  const openSession = sorted.find((s) => s.status === "open");

  function moveBefore(targetId: number) {
    if (draggedId === null || draggedId === targetId) return;
    setDraft((current) => {
      const sourceIndex = current.findIndex((item) => item.id === draggedId);
      const targetIndex = current.findIndex((item) => item.id === targetId);
      if (sourceIndex < 0 || targetIndex < 0) return current;
      const next = [...current];
      const [item] = next.splice(sourceIndex, 1);
      next.splice(targetIndex, 0, item);
      return next.map((session, index) => ({ ...session, order: index + 1 }));
    });
    setDirty(true);
  }

  async function saveOrder() {
    setSaving(true);
    try { await reorderLessons(String(courseId), draft.map((session) => session.id)); toast.success("Đã lưu thứ tự buổi học."); setDirty(false); onChanged?.(); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Không thể lưu thứ tự buổi học."); }
    finally { setSaving(false); }
  }

  if (sorted.length === 0) {
    return <EmptyState icon={CalendarPlus} title="Chưa có buổi học nào" description="Nhấn Tạo buổi học để bắt đầu." />;
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">Kéo thả để sắp xếp thứ tự buổi học.</p>
        <Button onClick={() => void saveOrder()} disabled={!dirty || saving} size="sm"><Save className="size-4" /> {saving ? "Đang lưu..." : "Lưu thứ tự"}</Button>
      </div>
      {openSession && <SessionAlertBanner session={openSession} studentCount={studentCount} />}
      {sorted.map((session) => {
        const dragProps = { draggable: true, onDragStart: () => setDraggedId(session.id), onDragOver: (event: DragEvent<HTMLSpanElement>) => event.preventDefault(), onDrop: () => { moveBefore(session.id); setDraggedId(null); }, onDragEnd: () => setDraggedId(null) };
        const handle = <span className="mr-2 inline-flex cursor-grab" title="Kéo để sắp xếp" {...dragProps}><GripVertical className="size-4 text-muted-foreground" /></span>;
        switch (session.status) {
          case "open":
            return <div key={session.id} className="flex items-center gap-2">{handle}<div className="min-w-0 flex-1"><OpenSessionCard session={session} courseId={courseId} studentCount={studentCount} onSelect={() => router.push(`/teacher/courses/${courseId}/sessions/${session.id}`)} /></div></div>;
          case "upcoming":
            return <div key={session.id} className="flex items-center gap-2">{handle}<div className="min-w-0 flex-1"><UpcomingSessionCard session={session} courseId={courseId} onSelect={() => router.push(`/teacher/courses/${courseId}/sessions/${session.id}`)} /></div></div>;
          case "closed":
            return <div key={session.id} className="flex items-center gap-2">{handle}<div className="min-w-0 flex-1"><ClosedSessionCard session={session} courseId={courseId} studentCount={studentCount} onSelect={() => router.push(`/teacher/courses/${courseId}/sessions/${session.id}`)} /></div></div>;
        }
      })}
    </div>
  );
}
