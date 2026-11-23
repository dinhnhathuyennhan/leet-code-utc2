"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Ban, Check, Loader2, Plus, Search, X } from "lucide-react";

import {
  ProblemGradingModeSelect,
  ProblemLevelSelect,
  type ProblemGradingModeFilter,
  type ProblemLevelFilter,
} from "@/components/shared/problem-filter-selects";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ProblemGradingMode, ProblemListItem } from "@/lib/api/endpoints/problems";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import { useInfiniteProblems } from "@/lib/hooks/use-problems";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 20;

const LEVEL_LABEL: Record<string, string> = { easy: "Dễ", medium: "Trung bình", hard: "Khó" };
const LEVEL_CLASS: Record<string, string> = {
  easy: "bg-emerald-50 text-emerald-700",
  medium: "bg-amber-50 text-amber-700",
  hard: "bg-red-50 text-red-700",
};
const GRADING_LABEL: Record<ProblemGradingMode, string> = { harness: "Harness", stdin_stdout: "stdin/stdout" };

/** Bài đã chọn: chỉ giữ đủ thông tin để hiển thị chip, kể cả khi bài không còn nằm trong kết quả lọc. */
export interface PickedProblem {
  id: number;
  title: string;
  code: string | null;
}

interface ProblemBankPickerProps {
  /** Mã lớp học: nhóm "Bài trong lớp học này" lấy bài đã gắn vào các buổi của lớp. */
  courseId: string;
  enabled: boolean;
  selected: PickedProblem[];
  onToggle: (problem: PickedProblem) => void;
  deadlineLabel?: string;
  /** Nhãn buổi học của bài đã gắn (theo `lesson_id`), vd "Buổi 2". */
  lessonLabel?: (lessonId: number) => string | undefined;
  /** Trả lý do nếu bài không được chọn (vd đã có trong buổi), `null` nếu chọn được. */
  disabledReason?: (problem: ProblemListItem) => string | null;
  listClassName?: string;
}

/** Gọi `onVisible` khi phần tử cuối danh sách cuộn vào khung nhìn (cơ chế "kéo cuối trang để tải thêm"). */
function LoadMoreSentinel({ onVisible, root, disabled }: { onVisible: () => void; root: HTMLElement | null; disabled: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const callbackRef = useRef(onVisible);
  useEffect(() => { callbackRef.current = onVisible; }, [onVisible]);
  useEffect(() => {
    const node = ref.current;
    if (disabled || !node || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      (entries) => { if (entries.some((entry) => entry.isIntersecting)) callbackRef.current(); },
      { root, rootMargin: "80px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [disabled, root]);
  return <div ref={ref} aria-hidden className="h-px" />;
}

export function ProblemBankPicker({
  courseId,
  enabled,
  selected,
  onToggle,
  deadlineLabel,
  lessonLabel,
  disabledReason,
  listClassName,
}: ProblemBankPickerProps) {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<ProblemLevelFilter>("");
  const [gradingMode, setGradingMode] = useState<ProblemGradingModeFilter>("");
  const [scrollRoot, setScrollRoot] = useState<HTMLDivElement | null>(null);
  const debouncedQuery = useDebouncedValue(query, 300);

  const filters = {
    q: debouncedQuery.trim() || undefined,
    level: level || undefined,
    grading_mode: gradingMode || undefined,
    page_size: PAGE_SIZE,
  };
  // Bài đã gắn vào các buổi của lớp này (chọn lại sẽ được sao chép sang buổi mới) và bài trong ngân hàng.
  const courseProblems = useInfiniteProblems({ ...filters, course_id: courseId }, enabled);
  const bankProblems = useInfiniteProblems({ ...filters, bank_only: true, has_testcases: true }, enabled);

  const selectedIds = useMemo(() => new Set(selected.map((problem) => problem.id)), [selected]);

  const courseItems = courseProblems.data?.pages.flatMap((page) => page.items) ?? [];
  const bankItems = bankProblems.data?.pages.flatMap((page) => page.items) ?? [];
  const courseTotal = courseProblems.data?.pages[0]?.total ?? 0;
  const bankTotal = bankProblems.data?.pages[0]?.total ?? 0;
  const hasFilter = Boolean(filters.q || filters.level || filters.grading_mode);

  // Tải hết bài của lớp trước rồi mới tới ngân hàng, vì hai nhóm nằm nối tiếp nhau trong cùng khung cuộn.
  const courseDone = !courseProblems.hasNextPage;
  function loadMore() {
    if (!courseDone) {
      if (!courseProblems.isFetchingNextPage) void courseProblems.fetchNextPage();
    } else if (bankProblems.hasNextPage && !bankProblems.isFetchingNextPage) {
      void bankProblems.fetchNextPage();
    }
  }
  const canLoadMore = Boolean(courseProblems.hasNextPage || bankProblems.hasNextPage);
  const fetchingMore = courseProblems.isFetchingNextPage || bankProblems.isFetchingNextPage;
  const initialLoading = courseProblems.isPending || bankProblems.isPending;

  function renderItem(problem: ProblemListItem) {
    const isSelected = selectedIds.has(problem.id);
    // Bài chưa có testcase không gắn được vào buổi học (backend trả 422).
    const blocked = isSelected
      ? null
      : problem.total_number_testcase === 0 ? "Chưa có testcase" : disabledReason?.(problem) ?? null;
    const lessonText = problem.lesson_id !== null ? lessonLabel?.(problem.lesson_id) ?? "Buổi khác" : null;
    return (
      <button
        type="button"
        key={problem.id}
        aria-pressed={isSelected}
        disabled={Boolean(blocked)}
        title={blocked ?? undefined}
        onClick={() => onToggle({ id: problem.id, title: problem.title, code: problem.code })}
        className={cn(
          "flex w-full min-w-0 items-center justify-between gap-3 rounded-lg border px-3 py-3 text-left transition",
          isSelected ? "border-indigo-300 bg-white" : "border-transparent bg-white/60 hover:bg-white",
          blocked && "cursor-not-allowed opacity-50 hover:bg-white/60",
        )}
      >
        <span className="min-w-0 flex-1 space-y-1">
          <span className="flex min-w-0 flex-wrap items-center gap-1.5">
            <span className="rounded bg-indigo-100 px-1.5 py-0.5 font-mono text-xs whitespace-nowrap text-indigo-800">{problem.code ?? `Bài ${problem.id}`}</span>
            <strong className="break-words">{problem.title}</strong>
          </span>
          <span className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            <span className={cn("rounded px-1.5 py-0.5 font-medium", LEVEL_CLASS[problem.level] ?? "bg-slate-100 text-slate-700")}>{LEVEL_LABEL[problem.level] ?? problem.level}</span>
            <span className="rounded bg-slate-100 px-1.5 py-0.5 font-medium text-slate-700">{GRADING_LABEL[problem.grading_mode]}</span>
            {lessonText && <span className="rounded bg-violet-50 px-1.5 py-0.5 font-medium text-violet-700">{lessonText}</span>}
            <span className="break-words">{problem.total_number_testcase} test cases{deadlineLabel ? ` · Hạn ${deadlineLabel}` : ""}</span>
            {blocked && <span className="font-medium text-slate-600">· {blocked}</span>}
          </span>
        </span>
        {isSelected ? <Check className="size-4 shrink-0 text-emerald-600" /> : blocked ? <Ban className="size-4 shrink-0 text-slate-400" /> : <Plus className="size-4 shrink-0 text-slate-400" />}
      </button>
    );
  }

  const failed = courseProblems.isError || bankProblems.isError;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-0 flex-1 basis-56">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <Input value={query} onChange={(event) => setQuery(event.target.value)} className="h-9 pl-9" placeholder="Tìm mã hoặc tên bài..." aria-label="Tìm bài tập" />
        </div>
        <ProblemLevelSelect value={level} onChange={setLevel} />
        <ProblemGradingModeSelect value={gradingMode} onChange={setGradingMode} />
      </div>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5" aria-label="Bài đã chọn">
          {selected.map((problem) => (
            <span key={problem.id} className="inline-flex max-w-full items-center gap-1 rounded-full bg-indigo-100 py-0.5 pr-1 pl-2.5 text-xs text-indigo-900">
              <span className="truncate">{problem.code ? `${problem.code} · ` : ""}{problem.title}</span>
              <button type="button" onClick={() => onToggle(problem)} className="rounded-full p-0.5 hover:bg-indigo-200" aria-label={`Bỏ chọn ${problem.title}`}><X className="size-3" /></button>
            </span>
          ))}
        </div>
      )}

      <div ref={setScrollRoot} className={cn("max-h-[30vh] space-y-2 overflow-y-auto rounded-xl bg-indigo-50/70 p-3 sm:max-h-[360px]", listClassName)}>
        {initialLoading ? (
          <p className="py-6 text-center text-sm text-muted-foreground">Đang tải bài từ ngân hàng...</p>
        ) : failed && !courseItems.length && !bankItems.length ? (
          <p className="py-6 text-center text-sm text-red-600">Không tải được danh sách bài tập.</p>
        ) : !courseItems.length && !bankItems.length ? (
          <p className="py-6 text-center text-sm text-muted-foreground">{hasFilter ? "Không có bài tập phù hợp bộ lọc." : "Chưa có bài tập trong ngân hàng."}</p>
        ) : (
          <>
            {courseItems.length > 0 && (
              <>
                <p className="px-1 text-xs font-semibold text-muted-foreground uppercase">Bài trong lớp học này ({courseTotal})</p>
                {courseItems.map(renderItem)}
              </>
            )}
            {courseDone && bankItems.length > 0 && (
              <>
                <p className="px-1 pt-1 text-xs font-semibold text-muted-foreground uppercase">Ngân hàng bài ({bankTotal})</p>
                {bankItems.map(renderItem)}
              </>
            )}
            {canLoadMore && (
              <>
                <LoadMoreSentinel onVisible={loadMore} root={scrollRoot} disabled={fetchingMore} />
                <div className="flex justify-center pt-1">
                  <Button type="button" variant="ghost" size="sm" disabled={fetchingMore} onClick={loadMore}>
                    {fetchingMore ? <><Loader2 className="size-4 animate-spin" /> Đang tải thêm...</> : "Xem thêm"}
                  </Button>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
