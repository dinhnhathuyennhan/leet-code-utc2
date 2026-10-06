"use client";

import { CalendarPlus } from "lucide-react";

import { EmptyState } from "@/components/shared/page-state";

export function StudentCourseInfoPanel() {
  return (
    <div className="space-y-4">
      <EmptyState
        icon={CalendarPlus}
        title="Chưa có buổi học nào"
        description="Danh sách buổi học và bài tập sẽ đến ở Phase 2 (theo roadmap dự án)."
      />
    </div>
  );
}