"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { toast } from "sonner";
import { AdminProblemEditor } from "@/components/admin/admin-problem-editor";
import { Button } from "@/components/ui/button";
import {
  createLessonProblem,
  getSessionDetail,
  type ProblemCreateRequest,
} from "@/lib/api/endpoints/courses";
import type { SessionExercise } from "@/lib/types/course";

export function NewProblemModal({
  courseId,
  sessionId,
  startDate,
  endDate,
  onCreated,
  onClose,
  existingTitles,
}: {
  courseId: string;
  sessionId: string;
  startDate: string;
  endDate: string;
  onCreated: (exercise: SessionExercise) => void;
  onClose: () => void;
  existingTitles: string[];
}) {
  const [busy, setBusy] = useState(false);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[95dvh] w-full max-w-5xl overflow-y-auto rounded-2xl bg-card p-6">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-[#2f226b]">Thêm bài tập mới</h2>
            <p className="text-sm text-muted-foreground">
              Bài được tạo riêng cho buổi học này (không thêm vào ngân hàng bài
              chung). Lịch mở/đóng bài theo ngày của buổi học.
            </p>
          </div>
          <Button variant="ghost" size="icon" disabled={busy} onClick={onClose}>
            <X className="size-4" />
          </Button>
        </div>
        <AdminProblemEditor
          onBusyChange={setBusy}
          defaultStart={`${startDate}T00:00:00`}
          defaultEnd={`${endDate}T23:59:59`}
          onSave={async (payload) => {
            if (existingTitles.some((title) => title.trim().toLocaleLowerCase() === payload.title.trim().toLocaleLowerCase())) {
              throw new Error("Buổi học đã có bài trùng nội dung này.");
            }
            // Teacher tạo bài thẳng trong buổi học; ngân hàng bài chung chỉ Admin được thêm.
            const created = await createLessonProblem(courseId, sessionId, payload as ProblemCreateRequest);
            const refreshed = await getSessionDetail(courseId, sessionId);
            const attached = refreshed.exercises.find((item) => item.id === created.id);
            if (!attached) throw new Error("Không tìm thấy bài tập vừa thêm vào buổi học.");
            onCreated({ ...attached, order: 1 });
            toast.success("Đã tạo bài tập mới.");
            onClose();
          }}
        />
      </div>
    </div>
  );
}
