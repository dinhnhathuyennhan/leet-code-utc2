"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/shared/page-state";
import { ApiError } from "@/lib/api/error";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { getAdminBankProblem, updateAdminBankProblem, deleteAdminBankProblem, updateAdminProblem, deleteAdminProblem } from "@/lib/api/endpoints/admin-management";
import { adminKeys } from "@/lib/hooks/use-admin";
import type { AdminProblem, AdminProblemPayload } from "@/lib/types/admin";
import { AdminProblemEditor } from "./admin-problem-editor";
import { AdminProblemTestcases } from "./admin-problem-testcases";
import { AdminProblemPreview } from "./admin-problem-preview";
import { AdminConfirm, AdminHeading, AdminLoading, ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

function changedFields(problem: AdminProblem, payload: AdminProblemPayload): Partial<AdminProblemPayload> {
  const existingTests = problem.testcases.map(({ input, expected_output, is_sample }) => ({ input, expected_output, is_sample }));
  return {
    ...(payload.title !== problem.title && { title: payload.title }),
    ...(payload.function_name !== problem.function_name && { function_name: payload.function_name }),
    ...(payload.description !== problem.description && { description: payload.description }),
    ...(payload.constraints !== problem.constraints && { constraints: payload.constraints }),
    ...(payload.level !== problem.level && { level: payload.level }),
    ...(payload.time_limit_seconds !== problem.time_limit_seconds && { time_limit_seconds: payload.time_limit_seconds }),
    ...(payload.hint !== problem.hint && { hint: payload.hint }),
    ...(payload.complexity !== problem.complexity && { complexity: payload.complexity }),
    ...(new Date(payload.start_datetime).getTime() !== new Date(problem.start_datetime).getTime() && { start_datetime: payload.start_datetime }),
    ...(new Date(payload.end_datetime).getTime() !== new Date(problem.end_datetime).getTime() && { end_datetime: payload.end_datetime }),
    ...((payload.function_name !== problem.function_name || ["python", "c", "cpp", "java"].some((language) => payload.starter_codes[language] !== problem.starter_codes[language])) && { starter_codes: payload.starter_codes }),
    ...(JSON.stringify(payload.testcases) !== JSON.stringify(existingTests) && { testcases: payload.testcases }),
  };
}

function LegacyProblemEditor({ problem, onSave }: { problem: AdminProblem; onSave: (data: Partial<AdminProblemPayload>) => Promise<void> }) {
  const [title, setTitle] = useState(problem.title);
  const [description, setDescription] = useState(problem.description);
  const [constraints, setConstraints] = useState(problem.constraints);
  const [level, setLevel] = useState(problem.level);
  const [hint, setHint] = useState(problem.hint ?? "");
  const [complexity, setComplexity] = useState(problem.complexity ?? "");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const data: Partial<AdminProblemPayload> = {
      ...(title.trim() !== problem.title && { title: title.trim() }),
      ...(description !== problem.description && { description }),
      ...(constraints !== problem.constraints && { constraints }),
      ...(level !== problem.level && { level: level as AdminProblemPayload["level"] }),
      ...((hint.trim() || null) !== problem.hint && { hint: hint.trim() || null }),
      ...((complexity.trim() || null) !== problem.complexity && { complexity: complexity.trim() || null }),
    };
    if (!Object.keys(data).length) { toast.info("Không có thay đổi để lưu."); return; }
    setBusy(true);
    try { await onSave(data); } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <section className="space-y-5 rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
    <p className="text-sm text-muted-foreground">Đề cũ dùng testcase stdin/stdout hoặc thiếu mã mẫu cho các ngôn ngữ. Bạn có thể sửa nội dung đề ở đây và quản lý testcase ở phần bên dưới.</p>
    <form onSubmit={(event) => void submit(event)} className="space-y-4">
      <fieldset disabled={busy} className="space-y-4">
        <label className="block space-y-2 text-sm font-medium">Tên đề<Input value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={255} /></label>
        <label className="block space-y-2 text-sm font-medium">Mô tả<Textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={5} /></label>
        <label className="block space-y-2 text-sm font-medium">Ràng buộc<Textarea value={constraints} onChange={(event) => setConstraints(event.target.value)} rows={3} /></label>
        <label className="block space-y-2 text-sm font-medium">Độ khó<select value={level} onChange={(event) => setLevel(event.target.value)} className={`${ADMIN_SELECT} w-full`}><option value="easy">Dễ</option><option value="medium">Trung bình</option><option value="hard">Khó</option></select></label>
        <label className="block space-y-2 text-sm font-medium">Gợi ý<Textarea value={hint} onChange={(event) => setHint(event.target.value)} /></label>
        <label className="block space-y-2 text-sm font-medium">Độ phức tạp<Input value={complexity} onChange={(event) => setComplexity(event.target.value)} /></label>
      </fieldset>
      <Button type="submit" disabled={busy} className={ADMIN_PRIMARY}>{busy ? "Đang lưu..." : "Lưu nội dung đề"}</Button>
    </form>
    <div className="space-y-3 border-t pt-4"><h2 className="font-semibold">Mã khởi tạo hiện có</h2><pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-4 font-mono text-xs text-slate-100">{problem.starter_codes?.python || problem.starter_code}</pre></div>
  </section>;
}

export function AdminBankProblemDetail({ id }: { id: number }) {
  const client = useQueryClient();
  const router = useRouter();
  const query = useQuery({
    queryKey: [...adminKeys.problems, "detail", id],
    queryFn: () => getAdminBankProblem(id),
    retry: (count, error) => !(error instanceof ApiError && [403, 404].includes(error.status)) && count < 3,
  });
  if (query.isPending) return <AdminLoading />;
  if (query.error || !query.data) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  const problem = query.data;
  const attached = problem.lesson_id !== null && problem.course_id !== null;
  const legacy = !problem.function_name || ["python", "c", "cpp", "java"].some((language) => !problem.starter_codes?.[language]?.trim()) || problem.testcases.some((test) => !Array.isArray(test.input));
  const lessonId = String(problem.lesson_id);
  const courseId = problem.course_id ?? "";
  return <div className="space-y-6">
    <Link href="/admin/problem-bank" className="inline-flex items-center gap-2 text-sm text-indigo-700 dark:text-indigo-300"><ArrowLeft className="size-4" />Quay lại ngân hàng đề</Link>
    <AdminHeading title={problem.title} description={attached ? `Bài tập #${id} · ${courseId} · Buổi #${lessonId}` : `Đề nguồn #${id}`} actions={<>
      {attached && <Button asChild variant="outline"><Link href={`/admin/courses/${encodeURIComponent(courseId)}/sessions/${lessonId}`}>Xem buổi học</Link></Button>}
      <AdminConfirm label="Xóa đề" title="Xóa bài tập?" description={attached ? "Bài tập sẽ bị xóa khỏi buổi học. Đề nguồn và bản sao ở các buổi khác vẫn được giữ." : "Đề nguồn này sẽ bị xóa. Bản sao đã gắn vào buổi học vẫn được giữ."} onConfirm={async () => {
        if (attached) await deleteAdminProblem(courseId, lessonId, id);
        else await deleteAdminBankProblem(id);
        await client.invalidateQueries({ queryKey: adminKeys.all });
        toast.success("Đã xóa bài tập.");
        router.push("/admin/problem-bank");
      }} />
    </>} />
    <section className="space-y-2 rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
      <h2 className="font-semibold">Nội dung đề bài</h2>
      <p className="whitespace-pre-wrap text-sm leading-6">{problem.description}</p>
      {problem.constraints && <><h3 className="pt-2 text-sm font-semibold">Ràng buộc</h3><p className="whitespace-pre-wrap text-sm">{problem.constraints}</p></>}
      <p className="text-xs text-muted-foreground">{problem.total_number_testcase} testcase · {problem.level} · Giới hạn {problem.time_limit_seconds} giây</p>
    </section>
    {legacy ? <LegacyProblemEditor key={`legacy-editor-${query.dataUpdatedAt}`} problem={problem} onSave={async (data) => {
      if (attached) await updateAdminProblem(courseId, lessonId, String(id), data);
      else await updateAdminBankProblem(id, data);
      await client.invalidateQueries({ queryKey: adminKeys.problems });
      toast.success("Đã lưu nội dung đề.");
    }} /> : <section className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6"><AdminProblemEditor key={`problem-editor-${query.dataUpdatedAt}`} problem={problem} hideTestcases onSave={async (payload) => {
      const changes = changedFields(problem, payload);
      if (!Object.keys(changes).length) { toast.info("Không có thay đổi để lưu."); return; }
      if (attached) await updateAdminProblem(courseId, lessonId, String(id), changes);
      else await updateAdminBankProblem(id, changes);
      await client.invalidateQueries({ queryKey: adminKeys.problems });
      toast.success("Đã lưu bài tập.");
    }} /></section>}
    <AdminProblemTestcases problem={problem} onChanged={async () => { await client.invalidateQueries({ queryKey: adminKeys.problems }); }} />
    <AdminProblemPreview key={`problem-preview-${query.dataUpdatedAt}`} problem={problem} />
  </div>;
}
