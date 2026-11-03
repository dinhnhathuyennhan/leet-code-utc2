import type { StudentSubmissionStatus } from "@/lib/types/submission";
import type { TranslationKey } from "@/lib/i18n";

export interface StatusMeta {
  label: string;
  /** Key tra cứu bản dịch — dùng để hiển thị đúng ngôn ngữ đang chọn. */
  labelKey: TranslationKey;
  /** Badge / chip classes. */
  className: string;
  /** Icon component từ lucide-react. */
  icon: "check" | "x" | "alert" | "clock" | "bug" | "loader";
}

/**
 * Nhãn + màu cho từng trạng thái bài nộp.
 *
 * Backend trả về status đã chuẩn hoá (accepted / wrong_answer / compile_error /
 * runtime_error / time_limit_exceeded / internal_error / error / pending).
 */
export const SUBMISSION_STATUS: Record<StudentSubmissionStatus, StatusMeta> = {
  accepted: {
    label: "Đạt",
    labelKey: "status.accepted",
    className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300",
    icon: "check",
  },
  wrong_answer: {
    label: "Sai kết quả",
    labelKey: "status.wrongAnswer",
    className: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300",
    icon: "x",
  },
  compile_error: {
    label: "Lỗi biên dịch",
    labelKey: "status.compileError",
    className: "bg-orange-100 text-orange-800 dark:bg-orange-500/20 dark:text-orange-300",
    icon: "alert",
  },
  runtime_error: {
    label: "Lỗi khi chạy",
    labelKey: "status.runtimeError",
    className: "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300",
    icon: "bug",
  },
  time_limit_exceeded: {
    label: "Quá thời gian",
    labelKey: "status.timeLimitExceeded",
    className: "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300",
    icon: "clock",
  },
  internal_error: {
    label: "Lỗi hệ thống",
    labelKey: "status.internalError",
    className: "bg-slate-100 text-slate-700 dark:bg-slate-500/20 dark:text-slate-300",
    icon: "alert",
  },
  error: {
    label: "Lỗi",
    labelKey: "status.error",
    className: "bg-slate-100 text-slate-700 dark:bg-slate-500/20 dark:text-slate-300",
    icon: "alert",
  },
  pending: {
    label: "Đang chờ chấm",
    labelKey: "status.pending",
    className: "bg-sky-100 text-sky-800 dark:bg-sky-500/20 dark:text-sky-300",
    icon: "loader",
  },
  processing: {
    label: "Đang chấm",
    labelKey: "status.processing",
    className: "bg-sky-100 text-sky-800 dark:bg-sky-500/20 dark:text-sky-300",
    icon: "loader",
  },
};

const FALLBACK: StatusMeta = {
  label: "Không rõ",
  labelKey: "status.unknown",
  className: "bg-slate-100 text-slate-700 dark:bg-slate-500/20 dark:text-slate-300",
  icon: "alert",
};

/** Lấy metadata của một status, có fallback cho status lạ (dữ liệu cũ). */
export function submissionStatusMeta(status: string): StatusMeta {
  return SUBMISSION_STATUS[status as StudentSubmissionStatus] ?? {
    ...FALLBACK,
    label: status || FALLBACK.label,
  };
}

/**
 * Bài nộp được "Review code" bằng AI khi đã pass TOÀN BỘ testcase.
 *
 * Khớp điều kiện backend (`is_fully_accepted`): status accepted, bài có ít nhất
 * một testcase và số test đạt bằng tổng số test.
 */
export function canReviewCode(submission: {
  status: string;
  passed_count: number;
  total_testcases: number;
} | null | undefined): boolean {
  if (!submission) return false;
  return (
    submission.status === "accepted" &&
    submission.total_testcases > 0 &&
    submission.passed_count >= submission.total_testcases
  );
}

/** Điểm quy đổi ra thang 10 từ số testcase đạt. */
export function scoreOutOfTen(passed: number, total: number): number | null {
  if (!total) return null;
  return Math.round((passed / total) * 10 * 10) / 10;
}
