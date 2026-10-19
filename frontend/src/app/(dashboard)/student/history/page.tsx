"use client";

import { Clock } from "lucide-react";

import { EmptyState } from "@/components/shared/page-state";

/**
 * Trang lịch sử nộp bài — placeholder cho Phase 3 (Submission).
 *
 * Phase 3 (theo `docs/roadmap.md § Phase 3`, dự kiến 21/10 → 03/11) mới
 * implement `GET /problems/{id}/submissions` + `GET /submissions/{id}`.
 *
 * Hiện tại chỉ hiện EmptyState để menu sidebar không trỏ vào 404 —
 * khi Phase 3 xong, file này sẽ được thay thế bằng danh sách + filter
 * + panel chi tiết submission (code, verdict từng testcase, runtime…).
 */
export default function SubmissionHistoryPage() {
  return (
    <EmptyState
      icon={Clock}
      title="Lịch sử nộp bài"
      description="Tính năng này đang được phát triển trong giai đoạn tiếp theo (Phase 3 — Submission + chấm bài). Bạn sẽ thấy lịch sử các bài đã nộp, kết quả chấm từng testcase và thời gian chạy tại đây."
    />
  );
}
