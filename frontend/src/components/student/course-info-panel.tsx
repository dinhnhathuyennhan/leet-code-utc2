"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, Code2, FileText, Lock, PlayCircle } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Panel thông tin lớp theo design Figma "Modern Minimal + Developer Tool".
 *
 * Cấu trúc:
 *  - Danh sách "Buổi học" (Sessions) dạng accordion.
 *  - Mỗi buổi có deadline, danh sách bài tập dạng bảng (mã bài, trạng thái, điểm, hành động).
 *  - Buổi đã đóng: hiện kết quả + điểm.
 *  - Buổi sắp mở: hiện ngày mở + khóa.
 *  - Buổi đang mở: hiện deadline + bảng bài tập + nút "Làm bài / Xem bài".
 *
 * Hiện đang dùng dữ liệu MẪU (mock) — mỗi buổi chỉ 1 bài tập duy nhất
 * theo yêu cầu "chỉ cần 1 bài tập để chuyển qua giao diện coding".
 */

type SessionStatus = "open" | "closed" | "upcoming";
type AssignmentStatus = "not_started" | "submitted" | "graded";

interface StudentAssignment {
  id: string;
  code: string;
  title: string;
  status: AssignmentStatus;
  score: number | null; // 0-10
  maxScore: number;
}

interface StudentSession {
  id: string;
  number: number;
  title: string;
  status: SessionStatus;
  /** Deadline (cho open) hoặc ngày đóng (cho closed) hoặc ngày mở (cho upcoming). */
  importantDate: string; // ISO
  importantLabel: string;
  assignments: StudentAssignment[];
}

const SESSIONS: StudentSession[] = [
  {
    id: "s1",
    number: 1,
    title: "Buổi 1 — Làm quen với lập trình",
    status: "closed",
    importantDate: "2026-08-30T23:59:00",
    importantLabel: "Đã đóng ngày 30/08/2026",
    assignments: [
      {
        id: "1",
        code: "EX01",
        title: "In ra Hello World",
        status: "graded",
        score: 10,
        maxScore: 10,
      },
    ],
  },
  {
    id: "s2",
    number: 2,
    title: "Buổi 2 — Cấu trúc điều khiển & vòng lặp",
    status: "open",
    importantDate: "2026-09-18T23:59:00",
    importantLabel: "Hạn nộp 18/09/2024 · 23:59",
    assignments: [
      {
        id: "2",
        code: "EX02",
        title: "Số chẵn lẻ",
        status: "not_started",
        score: null,
        maxScore: 10,
      },
    ],
  },
  {
    id: "s3",
    number: 3,
    title: "Buổi 3 — Hàm và đệ quy",
    status: "upcoming",
    importantDate: "2026-10-05T00:00:00",
    importantLabel: "Mở lúc 05/10/2026 · 00:00",
    assignments: [
      {
        id: "3",
        code: "EX03",
        title: "Tính giai thừa (bằng đệ quy)",
        status: "not_started",
        score: null,
        maxScore: 10,
      },
    ],
  },
];

const STATUS_BADGE: Record<AssignmentStatus, { label: string; className: string }> = {
  not_started: {
    label: "Chưa làm",
    className: "bg-slate-100 text-slate-700",
  },
  submitted: {
    label: "Đã nộp",
    className: "bg-sky-100 text-sky-800",
  },
  graded: {
    label: "Đã chấm",
    className: "bg-emerald-100 text-emerald-800",
  },
};

const SESSION_INDICATOR: Record<SessionStatus, { label: string; className: string }> = {
  open: { label: "Đang mở", className: "bg-emerald-500" },
  closed: { label: "Đã đóng", className: "bg-slate-400" },
  upcoming: { label: "Sắp mở", className: "bg-amber-500" },
};

function AssignmentRow({
  assignment,
  sessionStatus,
  courseId,
}: {
  assignment: StudentAssignment;
  sessionStatus: SessionStatus;
  courseId: string;
}) {
  const locked = sessionStatus === "upcoming";
  const badge = STATUS_BADGE[assignment.status];
  const href = locked
    ? "#"
    : `/student/classes/${encodeURIComponent(courseId)}/assignments/${encodeURIComponent(assignment.id)}`;

  return (
    <tr className="border-t border-border/60 text-sm">
      <td className="py-3 pl-2 pr-2 font-mono text-xs font-semibold text-muted-foreground">
        {assignment.code}
      </td>
      <td className="py-3 pr-2">
        <span className="font-medium text-foreground">{assignment.title}</span>
      </td>
      <td className="py-3 pr-2">
        <span
          className={cn(
            "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
            badge.className,
          )}
        >
          {badge.label}
        </span>
      </td>
      <td className="py-3 pr-2 text-right tabular-nums">
        {assignment.score !== null ? (
          <span className="font-semibold text-emerald-700">
            {assignment.score.toFixed(1)}
            <span className="text-xs font-normal text-muted-foreground">
              /{assignment.maxScore}
            </span>
          </span>
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </td>
      <td className="py-3 pr-2 text-right">
        {locked ? (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
            <Lock className="size-3.5" />
            Chưa mở
          </span>
        ) : assignment.status === "not_started" ? (
          <Link
            href={href}
            className="inline-flex items-center gap-1 rounded-md bg-[#352078] px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[#2a1a60]"
          >
            <PlayCircle className="size-3.5" />
            Làm bài
          </Link>
        ) : (
          <Link
            href={href}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
          >
            <FileText className="size-3.5" />
            Xem bài
          </Link>
        )}
      </td>
    </tr>
  );
}

function SessionRow({
  session,
  isOpen,
  onToggle,
  courseId,
}: {
  session: StudentSession;
  isOpen: boolean;
  onToggle: () => void;
  courseId: string;
}) {
  const indicator = SESSION_INDICATOR[session.status];

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left transition-colors hover:bg-muted/40"
      >
        <div className="flex items-center gap-3">
          <span
            aria-hidden
            className={cn(
              "inline-block size-2.5 shrink-0 rounded-full",
              indicator.className,
            )}
          />
          <div>
            <div className="text-sm font-semibold text-foreground">
              {session.title}
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              {session.importantLabel}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden text-xs font-medium text-muted-foreground sm:inline">
            {indicator.label}
          </span>
          <ChevronDown
            className={cn(
              "size-4 text-muted-foreground transition-transform",
              isOpen && "rotate-180",
            )}
          />
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-border/60 bg-background/40 px-2 pb-2 pt-1">
          {session.assignments.length === 0 ? (
            <p className="px-3 py-4 text-sm text-muted-foreground">
              Buổi này chưa có bài tập.
            </p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="py-2 pl-2 pr-2 text-left font-medium">Mã bài</th>
                  <th className="py-2 pr-2 text-left font-medium">Tên bài</th>
                  <th className="py-2 pr-2 text-left font-medium">Trạng thái</th>
                  <th className="py-2 pr-2 text-right font-medium">Điểm</th>
                  <th className="py-2 pr-2 text-right font-medium">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {session.assignments.map((a) => (
                  <AssignmentRow
                    key={a.id}
                    assignment={a}
                    sessionStatus={session.status}
                    courseId={courseId}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

export function StudentCourseInfoPanel({ courseId }: { courseId: string }) {
  // Mặc định mở buổi đang "open" (Buổi 2)
  const defaultOpenId = SESSIONS.find((s) => s.status === "open")?.id ?? SESSIONS[0]?.id;
  const [openId, setOpenId] = useState<string | null>(defaultOpenId ?? null);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <Code2 className="size-4 text-[#352078]" />
        Danh sách buổi học &amp; bài tập
      </div>

      <div className="space-y-2">
        {SESSIONS.map((s) => (
          <SessionRow
            key={s.id}
            session={s}
            isOpen={openId === s.id}
            onToggle={() => setOpenId((cur) => (cur === s.id ? null : s.id))}
            courseId={courseId}
          />
        ))}
      </div>
    </div>
  );
}
