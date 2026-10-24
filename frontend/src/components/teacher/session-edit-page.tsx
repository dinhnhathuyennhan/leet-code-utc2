"use client";

import { useState } from "react";
import { CalendarDays, Check, Clock3, FileCode2, FlaskConical, Plus, Save, X } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { attachProblemsToLesson, createBankProblem, getSessionDetail, updateLesson } from "@/lib/api/endpoints/courses";
import { courseKeys } from "@/lib/hooks/use-courses";
import { toDateInput } from "@/lib/helpers/datetime";
import type { SessionDetailData, SessionExercise } from "@/lib/types/course";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SessionProblemEditor } from "./session-problem-editor";

// Modal tạo bài tập mới thủ công
function NewProblemModal({
  courseId,
  sessionId,
  startDate,
  endDate,
  onCreated,
  onClose,
}: {
  courseId: string;
  sessionId: string;
  startDate: string;
  endDate: string;
  onCreated: (exercise: SessionExercise) => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [functionName, setFunctionName] = useState("solution");
  const [description, setDescription] = useState("");
  const [constraints, setConstraints] = useState("");
  const [level, setLevel] = useState<"easy" | "medium" | "hard">("easy");
  const [timeLimit, setTimeLimit] = useState(1);
  const [starterCode, setStarterCode] = useState("");
  const [testcaseInput, setTestcaseInput] = useState("[]");
  const [testcaseOutput, setTestcaseOutput] = useState("0");
  const [hint, setHint] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleCreate() {
    if (!title.trim()) { toast.error("Tên bài tập không được để trống."); return; }
    let input: unknown[];
    let output: unknown;
    try { input = JSON.parse(testcaseInput); output = JSON.parse(testcaseOutput); if (!Array.isArray(input)) throw new Error(); } catch { toast.error("Testcase phải là JSON hợp lệ, input phải là mảng."); return; }
    setSaving(true);
    try {
      const payload = {
        title: title.trim(),
        description,
        constraints,
        level,
        time_limit_seconds: timeLimit,
        starter_code: starterCode,
        hint: hint || null,
        testcases: [{ input, expected_output: output, is_sample: true }],
      };
      const created = await createBankProblem({ ...payload, function_name: functionName.trim() || "solution", starter_codes: { python: starterCode || "# code", c: starterCode || "/* code */", cpp: starterCode || "// code", java: starterCode || "// code" }, start_datetime: `${startDate}T00:00:00+07:00`, end_datetime: `${endDate}T23:59:59+07:00`, testcases: [{ input, expected_output: output, is_sample: true }] });
      await attachProblemsToLesson(courseId, sessionId, [created.id]);
      const refreshed = await getSessionDetail(courseId, sessionId);
      const attached = refreshed.exercises.find((item) => item.title === created.title);
      if (!attached) throw new Error("Không tìm thấy bài tập vừa thêm vào buổi học.");
      const exercise: SessionExercise = { ...attached, order: 1 };
      onCreated(exercise);
      toast.success("Đã tạo bài tập mới.");
      onClose();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Không thể tạo bài tập.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,0.45)", display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem" }}>
      <div style={{ background: "#fff", borderRadius: "1rem", width: "min(96vw,680px)", maxHeight: "calc(100dvh - 2rem)", overflowY: "auto", display: "flex", flexDirection: "column" }}>
        <div style={{ borderBottom: "1px solid #e2e8f0", padding: "1.25rem 1.5rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h2 style={{ fontWeight: 700, fontSize: "1.1rem", color: "#2f226b" }}>Thêm bài tập thủ công</h2>
          <button type="button" onClick={onClose} style={{ cursor: "pointer", background: "none", border: "none", color: "#64748b" }}><X className="size-5" /></button>
        </div>
        <div style={{ padding: "1.25rem 1.5rem", display: "flex", flexDirection: "column", gap: "0.875rem" }}>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600 }}>
            Tên bài tập <span style={{ color: "red" }}>*</span>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Ví dụ: Tính tổng dãy số" style={{ marginTop: "0.25rem", background: "#eef2ff" }} />
          </label>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600 }}>Tên hàm<Input value={functionName} onChange={(e) => setFunctionName(e.target.value)} placeholder="solution" style={{ marginTop: "0.25rem", background: "#eef2ff" }} /></label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem" }}>
            <label style={{ fontSize: "0.75rem", fontWeight: 600 }}>
              Mức độ
              <select value={level} onChange={(e) => setLevel(e.target.value as "easy" | "medium" | "hard")} style={{ marginTop: "0.25rem", height: "2.25rem", width: "100%", borderRadius: "0.5rem", border: "1px solid #e2e8f0", background: "#eef2ff", padding: "0 0.5rem", fontSize: "0.875rem" }}>
                <option value="easy">Dễ</option>
                <option value="medium">Trung bình</option>
                <option value="hard">Khó</option>
              </select>
            </label>
            <label style={{ fontSize: "0.75rem", fontWeight: 600 }}>
              Giới hạn thời gian (s)
              <Input type="number" value={timeLimit} onChange={(e) => setTimeLimit(Number(e.target.value))} style={{ marginTop: "0.25rem", background: "#eef2ff" }} />
            </label>
            <div style={{ fontSize: "0.75rem", fontWeight: 600 }}>
              <span>Điểm tối đa</span>
              <div style={{ height: "2.25rem", background: "#eef2ff", borderRadius: "0.5rem", display: "flex", alignItems: "center", padding: "0 0.75rem", marginTop: "0.25rem", color: "#64748b", fontSize: "0.875rem" }}>Theo testcase</div>
            </div>
          </div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600 }}>
            Mô tả bài
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} style={{ marginTop: "0.25rem", background: "#eef2ff" }} placeholder="Trình bày đề bài..." />
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}><label style={{ fontSize: "0.75rem", fontWeight: 600 }}>Input testcase mẫu<textarea value={testcaseInput} onChange={(e) => setTestcaseInput(e.target.value)} rows={2} style={{ marginTop: "0.25rem", width: "100%", borderRadius: "0.5rem", border: "1px solid #e2e8f0", padding: "0.5rem" }} /></label><label style={{ fontSize: "0.75rem", fontWeight: 600 }}>Output testcase mẫu<textarea value={testcaseOutput} onChange={(e) => setTestcaseOutput(e.target.value)} rows={2} style={{ marginTop: "0.25rem", width: "100%", borderRadius: "0.5rem", border: "1px solid #e2e8f0", padding: "0.5rem" }} /></label></div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600 }}>
            Ràng buộc
            <Textarea value={constraints} onChange={(e) => setConstraints(e.target.value)} rows={2} style={{ marginTop: "0.25rem", background: "#eef2ff" }} placeholder="VD: 1 ≤ n ≤ 10^5" />
          </label>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600 }}>
            Gợi ý thuật toán (tuỳ chọn)
            <Textarea value={hint} onChange={(e) => setHint(e.target.value)} rows={2} style={{ marginTop: "0.25rem", background: "#eef2ff" }} placeholder="Gợi ý cách tiếp cận..." />
          </label>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600 }}>
            Mã nguồn khởi tạo (tuỳ chọn)
            <textarea value={starterCode} onChange={(e) => setStarterCode(e.target.value)} rows={4}
              style={{ marginTop: "0.25rem", width: "100%", borderRadius: "0.5rem", border: "1px solid #e2e8f0", background: "#0f172a", color: "#e2e8f0", padding: "0.75rem", fontFamily: "monospace", fontSize: "0.75rem" }}
              placeholder="def solution():\n    pass" />
          </label>
        </div>
        <div style={{ borderTop: "1px solid #e2e8f0", padding: "1rem 1.5rem", display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
          <Button variant="outline" onClick={onClose}>Huỷ bỏ</Button>
          <Button onClick={() => void handleCreate()} disabled={saving} style={{ background: "#2f226b", color: "#fff" }}>
            <Plus className="size-4" /> {saving ? "Đang tạo..." : "Tạo bài tập"}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function SessionEditPage({ courseId, sessionId, data, onSaved }: { courseId: string; sessionId: string; data: SessionDetailData; onSaved?: () => Promise<void> | void }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  // F4: Dùng toDateInput để lấy ngày theo giờ VN từ ISO string có offset
  const [title, setTitle] = useState(data.title);
  const [startDate, setStartDate] = useState(data.start_date ? toDateInput(data.start_date) : data.start_date);
  const [endDate, setEndDate] = useState(data.end_date ? toDateInput(data.end_date) : data.end_date);
  const [exercises, setExercises] = useState(data.exercises);
  const [selectedId, setSelectedId] = useState<number | null>(data.exercises[0]?.id ?? null);
  const [saving, setSaving] = useState(false);
  const [showNewProblem, setShowNewProblem] = useState(false);
  const [dateErrors, setDateErrors] = useState<{ start?: string; end?: string }>({});
  const selectedExercise = exercises.find((exercise) => exercise.id === selectedId) ?? exercises[0];

  async function saveSession() {
    const nextErrors: typeof dateErrors = {};
    if (!startDate) nextErrors.start = "Vui lòng chọn thời gian mở.";
    if (!endDate) nextErrors.end = "Vui lòng chọn hạn nộp.";
    if (startDate && endDate && startDate > endDate) nextErrors.end = "Hạn nộp phải sau hoặc bằng thời gian mở.";
    setDateErrors(nextErrors);
    if (!title.trim() || Object.keys(nextErrors).length) { if (!title.trim()) toast.error("Tên buổi học không được để trống."); return; }
    if (data.exercises.some((exercise) => exercise.submitted_count > 0) && startDate !== toDateInput(data.start_date)) {
      toast.error("Buổi học đã có bài nộp, không thể thay đổi thời gian bắt đầu.");
      return;
    }
    setSaving(true);
    try {
      const updatedCourse = await updateLesson(courseId, Number(sessionId), { lesson_name: title.trim(), start_date: startDate, end_date: endDate, problem_ids: exercises.map((exercise) => exercise.id) });
      queryClient.setQueryData(courseKeys.detail(courseId), updatedCourse);
      void queryClient.invalidateQueries({ queryKey: courseKeys.detail(courseId) });
      toast.success("Đã lưu thay đổi buổi học.");
      await onSaved?.();
      router.push(`/teacher/courses/${courseId}/sessions/${sessionId}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Không thể lưu buổi học.";
      if (/start|bắt đầu|mở/i.test(message)) setDateErrors({ start: message });
      else if (/end|hạn|kết thúc|nộp/i.test(message)) setDateErrors({ end: message });
      else toast.error(message);
    } finally { setSaving(false); }
  }

  function replaceExercise(updated: SessionExercise) {
    setExercises((current) => current.map((exercise) => exercise.id === updated.id ? updated : exercise));
  }

  function addNewExercise(exercise: SessionExercise) {
    const withOrder = { ...exercise, order: exercises.length + 1 };
    setExercises((current) => [...current, withOrder]);
    setSelectedId(exercise.id);
  }

  function removeExercise(problemId: number) {
    setExercises((current) => current.filter((exercise) => exercise.id !== problemId).map((exercise, index) => ({ ...exercise, order: index + 1 })));
    setSelectedId((current) => current === problemId ? null : current);
  }

  return <div className="space-y-5">
    {showNewProblem && (
      <NewProblemModal
        courseId={courseId}
        sessionId={sessionId}
        startDate={startDate}
        endDate={endDate}
        onCreated={addNewExercise}
        onClose={() => setShowNewProblem(false)}
      />
    )}

    <header className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Buổi {data.order}: {title} trong {data.course_name}</h1>
        <p className="text-xs text-muted-foreground">Mở - đóng: {startDate} → {endDate} · Sĩ số nộp: <strong>{data.submitted_students}/{data.total_students} SV</strong></p>
      </div>
      <div className="flex gap-2">
        <Button variant="outline" onClick={() => router.back()}><X className="size-4" /> Hủy bỏ</Button>
        <Button onClick={() => void saveSession()} disabled={saving} className="bg-[#2f226b] text-white"><Save className="size-4" /> {saving ? "Đang lưu..." : "Lưu buổi học"}</Button>
      </div>
    </header>

    <div className="grid gap-4 md:grid-cols-4">
      <InfoCard icon={<FileCode2 />} label="BÀI TẬP SẴN SÀNG" value={`${exercises.length} bài`} hint="Không tính assignment" />
      <InfoCard icon={<FlaskConical />} label="TỔNG TEST CASES" value={`${exercises.reduce((sum, item) => sum + item.total_number_testcase, 0)} test cases`} hint="Theo các bài đã chọn" />
      <InfoCard icon={<Clock3 />} label="ĐIỂM TỔNG BUỔI HỌC" value="Theo testcase" hint="Database chưa có cột điểm tối đa" />
      <InfoCard icon={<Check />} label="SỐ NGƯỜI ĐÃ NỘP" value={`${data.submitted_students} người thực hiện`} hint={`${startDate} → ${endDate}`} />
    </div>

    <div className="grid gap-5 xl:grid-cols-[270px_minmax(0,1fr)]">
      <aside className="h-fit space-y-4 rounded-xl border bg-card p-4 shadow-sm">
        <h2 className="font-bold text-[#2f226b]">CẤU HÌNH BUỔI HỌC</h2>
        <label className="block space-y-1 text-xs font-semibold">Tên buổi học<Input value={title} onChange={(event) => setTitle(event.target.value)} className="bg-indigo-50/70" /></label>
        <div className="grid grid-cols-2 gap-2">
          <label className="space-y-1 text-xs font-semibold">Thời gian mở<div className="relative"><CalendarDays className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-indigo-600" /><Input aria-invalid={Boolean(dateErrors.start)} disabled={data.exercises.some((exercise) => exercise.submitted_count > 0)} type="date" value={startDate} onChange={(event) => { setStartDate(event.target.value); setDateErrors((current) => ({ ...current, start: undefined, end: undefined })); }} className="bg-indigo-50/70 pl-7" /></div>{dateErrors.start && <p className="text-xs font-normal text-red-600">{dateErrors.start}</p>}{data.exercises.some((exercise) => exercise.submitted_count > 0) && <p className="text-xs font-normal text-amber-700">Đã có bài nộp: chỉ được thay đổi hạn nộp.</p>}</label>
          <label className="space-y-1 text-xs font-semibold">Hạn nộp<Input aria-invalid={Boolean(dateErrors.end)} type="date" value={endDate} onChange={(event) => { setEndDate(event.target.value); setDateErrors((current) => ({ ...current, end: undefined })); }} className="bg-indigo-50/70" />{dateErrors.end && <p className="text-xs font-normal text-red-600">{dateErrors.end}</p>}</label>
        </div>
        <div className="rounded-lg bg-indigo-50 p-3 text-xs text-muted-foreground">Thời gian và trạng thái được lấy từ Lesson trong database.</div>
        <div className="rounded-lg bg-red-50 p-3 text-xs leading-5 text-red-700">Các thay đổi về thời gian sẽ áp dụng cho tất cả sinh viên sau khi lưu.</div>
      </aside>

      <main className="space-y-5">
        <section className="space-y-3 rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold text-[#2f226b]">DANH SÁCH BÀI TẬP TRONG BUỔI</h2>
              <p className="text-xs text-muted-foreground">Bấm một bài tập để chỉnh nội dung phía dưới.</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded bg-[#2f226b] px-2 py-1 text-xs text-white">Ngân hàng đề UTC2</span>
              <Button
                size="sm"
                onClick={() => setShowNewProblem(true)}
                className="gap-1 bg-emerald-600 text-white hover:bg-emerald-700"
              >
                <Plus className="size-3.5" /> Thêm bài tập mới
              </Button>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {exercises.map((exercise) => (
              <button
                type="button"
                key={exercise.id}
                onClick={() => setSelectedId(exercise.id)}
                className={`rounded-lg border p-3 text-left transition ${selectedId === exercise.id ? "border-[#2f226b] bg-[#2f226b] text-white shadow-md" : "border-indigo-200 bg-indigo-50/70 text-slate-900"}`}
              >
                <p className="text-[10px] opacity-70">BÀI {exercise.order}</p>
                <p className="font-semibold">{exercise.title}</p>
                <p className="mt-2 text-xs opacity-70">{exercise.total_number_testcase} test cases · {exercise.level}</p>
                <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold"><Check className="size-3" /> Đang dùng</span>
              </button>
            ))}
            {exercises.length === 0 && (
              <div className="col-span-3 rounded-lg border-2 border-dashed border-indigo-200 p-6 text-center text-sm text-muted-foreground">
                Chưa có bài tập nào. Nhấn &ldquo;Thêm bài tập mới&rdquo; để bắt đầu.
              </div>
            )}
          </div>
        </section>

        {selectedExercise
          ? <SessionProblemEditor key={selectedExercise.id} courseId={courseId} sessionId={sessionId} exercise={selectedExercise} onSaved={replaceExercise} onDeleted={() => removeExercise(selectedExercise.id)} />
          : <section className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">Chọn một bài tập để bắt đầu chỉnh sửa.</section>
        }
      </main>
    </div>
  </div>;
}

function InfoCard({ icon, label, value, hint }: { icon: React.ReactNode; label: string; value: string; hint: string }) {
  return <div className="rounded-xl border bg-card p-4 shadow-sm"><div className="flex items-center justify-between text-indigo-700"><span className="text-[10px] font-bold tracking-wide">{label}</span>{icon}</div><p className="mt-2 text-xl font-bold text-[#2f226b]">{value}</p><p className="text-[11px] text-muted-foreground">{hint}</p></div>;
}
