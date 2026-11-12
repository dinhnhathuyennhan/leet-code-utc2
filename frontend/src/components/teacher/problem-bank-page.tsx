"use client";

import { useEffect, useState } from "react";
import { FileUp, Filter, Plus, Search, X } from "lucide-react";
import { toast } from "sonner";
import {
  getProblems,
  type ProblemListItem,
} from "@/lib/api/endpoints/problems";
import {
  createBankProblem,
  type ProblemCreateRequest,
} from "@/lib/api/endpoints/courses";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorState } from "@/components/shared/page-state";
import { ProblemImportDialog } from "@/components/shared/problem-import-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import { AdminProblemEditor } from "@/components/admin/admin-problem-editor";

const LEVELS = [
  { value: "", label: "Tất cả mức độ" },
  { value: "easy", label: "Dễ" },
  { value: "medium", label: "Trung bình" },
  { value: "hard", label: "Khó" },
] as const;
const GRADING_MODES = [
  { value: "", label: "Tất cả cách chấm" },
  { value: "harness", label: "Function-call (harness)" },
  { value: "stdin_stdout", label: "stdin/stdout" },
] as const;

export function ProblemBankPage() {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<"" | "easy" | "medium" | "hard">("");
  const [gradingMode, setGradingMode] = useState<
    "" | "harness" | "stdin_stdout"
  >("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<ProblemListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedProblem, setSelectedProblem] =
    useState<ProblemListItem | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const pageSize = 12;
  // Chờ người dùng gõ xong mới gọi API, thay vì bắn một request cho mỗi phím.
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    let active = true;
    void getProblems({
      q: debouncedQuery.trim() || undefined,
      level: level || undefined,
      grading_mode: gradingMode || undefined,
      page,
      page_size: pageSize,
    })
      .then((response) => {
        if (!active) return;
        setError(null);
        setItems(response.items);
        setTotal(response.total);
      })
      .catch((requestError) => {
        if (active) setError(requestError);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [debouncedQuery, level, gradingMode, page, refreshKey]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <section className="min-h-[calc(100dvh-110px)] rounded-xl bg-[#f8f9ff] shadow-sm">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b bg-card px-4 py-3 sm:px-6">
        <div>
          <h1 className="text-xl font-bold text-[#2f226b] sm:text-2xl">
            Ngân hàng bài
          </h1>
          <p className="text-sm text-muted-foreground">
            Danh sách bài từ backend, gồm bài dùng chung và bài thuộc các khóa
            học của bạn.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setImportOpen(true)}>
            <FileUp className="size-4" /> Import JSON
          </Button>
          <Button
            onClick={() => setCreateOpen(true)}
            className="bg-[#34227a] text-white"
          >
            <Plus className="size-4" /> Tạo bài
          </Button>
        </div>
      </header>
      <div className="m-4 flex flex-wrap items-center gap-3 rounded-xl bg-card p-3">
        <div className="relative min-w-0 flex-1 sm:min-w-64">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            className="h-9 pl-9"
            placeholder="Tìm mã hoặc tên bài..."
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="size-4 text-muted-foreground" />
          <select
            value={level}
            onChange={(event) => {
              setLevel(event.target.value as typeof level);
              setPage(1);
            }}
            className="h-9 rounded-md border bg-background px-3 text-sm"
          >
            {LEVELS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
        <select
          aria-label="Lọc cách chấm"
          value={gradingMode}
          onChange={(event) => {
            setGradingMode(event.target.value as typeof gradingMode);
            setPage(1);
          }}
          className="h-9 rounded-md border bg-background px-3 text-sm"
        >
          {GRADING_MODES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>
      {loading ? (
        <div className="grid gap-4 px-4 pb-6 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-36 rounded-xl" />
          ))}
        </div>
      ) : error ? (
        <div className="p-4">
          <ErrorState
            error={error}
            onRetry={() => setRefreshKey((current) => current + 1)}
          />
        </div>
      ) : (
        <>
          <div className="grid gap-4 px-4 pb-6 md:grid-cols-2 xl:grid-cols-3">
            {items.map((problem) => (
              <ProblemCard
                key={problem.id}
                problem={problem}
                onClick={() => setSelectedProblem(problem)}
              />
            ))}
            {!items.length && (
              <div className="col-span-full rounded-xl bg-card p-10 text-center text-sm text-muted-foreground">
                Không tìm thấy bài phù hợp.
              </div>
            )}
          </div>
          <footer className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-4 text-sm text-muted-foreground">
            <span>
              {total} bài · Trang {page}/{totalPages}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((current) => current - 1)}
              >
                Trang trước
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((current) => current + 1)}
              >
                Trang sau
              </Button>
            </div>
          </footer>
        </>
      )}
      {selectedProblem && (
        <ProblemPreview
          problem={selectedProblem}
          onClose={() => setSelectedProblem(null)}
        />
      )}
      <ProblemImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onImported={(result) => {
          setImportOpen(false);
          setQuery("");
          setLevel("");
          setGradingMode("");
          setPage(1);
          setRefreshKey((current) => current + 1);
          toast.success(`Đã import ${result.created_count} problem.`);
        }}
        onImportOutcomeUncertain={() => {
          setImportOpen(false);
          setQuery("");
          setLevel("");
          setGradingMode("");
          setPage(1);
          setRefreshKey((current) => current + 1);
          toast.error(
            "Chưa nhận được xác nhận import. Danh sách đang được tải lại; hãy kiểm tra trước khi gửi lại vì bài có thể đã được lưu.",
          );
        }}
      />
      {createOpen && (
        <BankProblemCreateDialog
          onClose={() => setCreateOpen(false)}
          onCreated={() => {
            setCreateOpen(false);
            setRefreshKey((current) => current + 1);
          }}
        />
      )}
    </section>
  );
}

function ProblemCard({
  problem,
  onClick,
}: {
  problem: ProblemListItem;
  onClick: () => void;
}) {
  const level =
    problem.level === "easy"
      ? "Dễ"
      : problem.level === "hard"
        ? "Khó"
        : "Trung bình";
  return (
    <button
      type="button"
      onClick={onClick}
      className="min-w-0 rounded-xl bg-card p-4 text-left shadow-sm transition hover:ring-2 hover:ring-indigo-300"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-mono text-xs text-indigo-700">
            {problem.code ?? `Problem #${problem.id}`}
          </p>
          <h2
            className="mt-1 truncate font-bold text-slate-900"
            title={problem.title}
          >
            {problem.title}
          </h2>
        </div>
        <span className="shrink-0 rounded px-2 py-0.5 text-xs font-semibold bg-indigo-50 text-indigo-700">
          {level}
        </span>
      </div>
      <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
        <span>{problem.total_number_testcase} testcase</span>
        <span>
          {problem.lesson_id === null ? "Ngân hàng chung" : "Đã gắn lớp"}
        </span>
      </div>
      <p className="mt-3 text-xs font-medium text-indigo-700">Xem chi tiết</p>
    </button>
  );
}

function ProblemPreview({
  problem,
  onClose,
}: {
  problem: ProblemListItem;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg space-y-4 rounded-2xl bg-card p-6 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-mono text-xs text-indigo-700">
              {problem.code ?? `Problem #${problem.id}`}
            </p>
            <h2 className="text-xl font-bold">{problem.title}</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <p>
            <span className="text-muted-foreground">Mức độ:</span>{" "}
            {problem.level}
          </p>
          <p>
            <span className="text-muted-foreground">Testcase:</span>{" "}
            {problem.total_number_testcase}
          </p>
          <p className="col-span-2">
            <span className="text-muted-foreground">Nguồn:</span>{" "}
            {problem.lesson_id === null
              ? "Ngân hàng chung (lesson_id = null)"
              : "Bài đã gắn lesson"}
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          Bài trong ngân hàng được giữ nguyên nguồn. Khi thêm vào buổi học,
          frontend sẽ gửi id nguồn qua API attach để backend tạo bản sao riêng.
        </p>
      </div>
    </div>
  );
}

function BankProblemCreateDialog({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [busy, setBusy] = useState(false);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[95dvh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-card p-6">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Tạo bài trong ngân hàng</h2>
            <p className="text-sm text-muted-foreground">
              Cần 10–50 testcase, ít nhất 3 mẫu và 5 hidden.
            </p>
          </div>
          <Button variant="ghost" size="icon" disabled={busy} onClick={onClose}>
            <X className="size-4" />
          </Button>
        </div>
        <AdminProblemEditor
          onBusyChange={setBusy}
          onSave={async (payload) => {
            await createBankProblem(payload as ProblemCreateRequest);
            toast.success("Đã tạo bài trong ngân hàng (lesson_id = null).");
            onCreated();
          }}
        />
      </div>
    </div>
  );
}
