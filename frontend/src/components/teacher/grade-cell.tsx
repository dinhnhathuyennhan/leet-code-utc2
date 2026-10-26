import type { GradeScoreValue, GradeSessionColumn } from "@/lib/types/course";

export function normalizeGradeScore(score: GradeScoreValue | undefined): number | null {
  if (score == null) return null;
  return typeof score === "number" ? score : score.value;
}

export function isSimilarGrade(score: GradeScoreValue | undefined): boolean {
  return typeof score === "object" && score !== null && score.is_similar === true;
}

export function isOverriddenGrade(score: GradeScoreValue | undefined): boolean {
  return typeof score === "object" && score !== null
    && (score.is_overridden === true || score.manual_score !== null && score.manual_score !== undefined);
}

export function hasSubmittedGrade(score: GradeScoreValue | undefined): boolean {
  return typeof score === "object" && score !== null ? score.submitted === true : normalizeGradeScore(score) !== null;
}

// SỬA: Chỉ tô đỏ tên khi chưa có điểm dương nào; một buổi chưa làm chỉ đỏ các ô thiếu.
// Quy tắc này cũng bắt được trường hợp toàn bộ điểm là 0 mà không phụ thuộc thứ tự dòng.
export function hasMeaningfulGrade(rowScores: Record<string, GradeScoreValue[]> | undefined, sessions: GradeSessionColumn[]): boolean {
  return sessions.some((session) => (rowScores?.[String(session.id)] ?? []).some((score) => {
    const value = normalizeGradeScore(score);
    return hasSubmittedGrade(score) && value !== null && value > 0;
  }));
}

export function sessionAverage(scores: GradeScoreValue[] | undefined): string {
  const values = (scores ?? []).map((score) => normalizeGradeScore(score) ?? 0);
  return values.length ? (values.reduce((sum, score) => sum + score, 0) / values.length).toFixed(1) : "0.0";
}

export function GradeCell({ score, suppressWarning = false }: { score: GradeScoreValue | undefined; suppressWarning?: boolean }) {
  const value = normalizeGradeScore(score);
  const className = suppressWarning
    ? "text-indigo-950"
    : isSimilarGrade(score)
    ? "bg-yellow-100 text-yellow-900"
    : value === null || value < 5
      ? "bg-red-100 text-red-700"
      : "text-indigo-950";
  return <span className={`inline-flex min-w-10 items-center justify-center rounded px-1.5 py-1 font-semibold ${className}`}>{value === null ? "–" : `${value.toFixed(1)}${isOverriddenGrade(score) ? "*" : ""}`}</span>;
}
