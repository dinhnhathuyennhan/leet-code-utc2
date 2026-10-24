"use client";

import { useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Download,
  FileSpreadsheet,
  Loader2,
  Plus,
  Search,
  Trash2,
  UserPlus,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import {
  addClassToCourse,
  addStudentToCourse,
  deleteStudentFromCourse,
} from "@/lib/api/endpoints/courses";
import { importStudents } from "@/lib/api/endpoints/admin";
import { downloadCsv } from "@/lib/helpers/download";
import { useClassStudents, useClasses } from "@/lib/hooks/use-courses";
import type { CourseStudent } from "@/lib/types/course";

export function CourseStudentsTable({
  students,
  courseId,
  onChanged,
}: {
  students: CourseStudent[];
  courseId: string;
  onChanged?: () => void;
}) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"class" | "individual">("class");
  const [query, setQuery] = useState("");
  const [studentId, setStudentId] = useState("");
  const [classId, setClassId] = useState("");
  const classes = useClasses(open && mode === "class");
  const classStudents = useClassStudents(classId, open && mode === "class");
  const enrolled = useMemo(
    () => new Set(students.map((s) => s.student_id)),
    [students],
  );
  const candidates = (classStudents.data ?? []).filter(
    (s) => !enrolled.has(s.user_id),
  );
  const rows = students.filter((s) =>
    `${s.student_id} ${s.full_name} ${s.email}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  const [importing, setImporting] = useState(false);
  const [adding, setAdding] = useState(false);
  const addingRef = useRef(false);
  const [pendingDelete, setPendingDelete] = useState<CourseStudent | null>(null);
  const [deleting, setDeleting] = useState(false);
  async function importFile(file: File) {
    setImporting(true);
    try {
      const result = await importStudents(file);
      const importedStudentIds = [
        ...result.created.map((student) => student.user_id),
        ...result.skipped.map((student) => student.user_id),
      ];
      await Promise.all(
        importedStudentIds.map((studentId) =>
          addStudentToCourse(courseId, studentId),
        ),
      );
      await refresh();
      toast.success(
        `Đã thêm ${importedStudentIds.length} sinh viên vào lớp; bỏ qua ${result.errors.length} dòng lỗi.`,
      );
      if (result.errors.length)
        toast.warning(`Có ${result.errors.length} dòng không hợp lệ.`);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Không thể import sinh viên.",
      );
    } finally {
      setImporting(false);
    }
  }
  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["courses"] });
    onChanged?.();
  }
  async function add() {
    if (addingRef.current) return;
    addingRef.current = true;
    setAdding(true);
    try {
      if (mode === "class") {
        const result = await addClassToCourse(courseId, classId);
        toast.success(`Đã thêm ${result.added_count} sinh viên.`);
      } else {
        await addStudentToCourse(courseId, studentId.trim());
        toast.success("Đã thêm sinh viên.");
      }
      await refresh();
      setOpen(false);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Không thể thêm sinh viên.",
      );
    } finally { addingRef.current = false; setAdding(false); }
  }
  async function remove(student: CourseStudent) {
    setPendingDelete(student);
  }
  async function confirmRemove() {
    if (!pendingDelete || deleting) return;
    setDeleting(true);
    try {
      await deleteStudentFromCourse(courseId, pendingDelete.student_id);
      await refresh();
      toast.success("Đã xóa sinh viên.");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Không thể xóa sinh viên.",
      );
    } finally { setDeleting(false); setPendingDelete(null); }
  }
  return (
    <section className="space-y-4 rounded-xl bg-card p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-9 pl-9"
            placeholder="Tìm MSSV, họ tên, email..."
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            className="hidden"
            id={`student-import-${courseId}`}
            type="file"
            accept=".xls,.xlsx"
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (file) void importFile(file);
            }}
          />
          <Button
            variant="outline"
            disabled={importing}
            onClick={() =>
              document.getElementById(`student-import-${courseId}`)?.click()
            }
          >
            <FileSpreadsheet className="size-4" />{" "}
            {importing ? "Đang import..." : "Import sinh viên"}
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              downloadCsv(`sinh-vien-${courseId}.csv`, [
                ["MSSV", "Họ tên", "Email", "Tiến độ (%)"],
                ...students.map((s) => [
                  s.student_id,
                  s.full_name,
                  s.email,
                  s.progress_percent,
                ]),
              ])
            }
          >
            <Download className="size-4" /> Xuất danh sách
          </Button>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger
              render={
                <Button className="bg-[#34227a] text-white">
                  <UserPlus className="size-4" /> Thêm sinh viên
                </Button>
              }
            />
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Thêm sinh viên vào lớp</DialogTitle>
                <DialogDescription>
                  Chọn lớp hành chính hoặc nhập MSSV.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant={mode === "class" ? "default" : "outline"}
                    onClick={() => setMode("class")}
                  >
                    Theo lớp
                  </Button>
                  <Button
                    variant={mode === "individual" ? "default" : "outline"}
                    onClick={() => setMode("individual")}
                  >
                    Nhập MSSV
                  </Button>
                </div>
                {mode === "class" ? (
                  <>
                    <select
                      value={classId}
                      onChange={(e) => setClassId(e.target.value)}
                      className="h-10 w-full rounded-md border px-3"
                    >
                      <option value="">Chọn lớp hành chính</option>
                      {(classes.data ?? []).map((item) => (
                        <option key={item.class_id} value={item.class_id}>
                          {item.class_id} — {item.department}
                        </option>
                      ))}
                    </select>
                    {classes.error && (
                      <p className="text-sm text-red-600">
                        Không tải được danh sách lớp.
                      </p>
                    )}
                    {classId && classStudents.error && (
                      <p className="text-sm text-red-600">
                        Không tải được danh sách sinh viên của lớp.
                      </p>
                    )}
                    <div className="max-h-56 overflow-auto rounded border p-2">
                      {classStudents.isPending
                        ? "Đang tải..."
                        : candidates.map((s) => (
                            <div
                              key={s.user_id}
                              className="border-b p-2 text-sm"
                            >
                              <strong>{s.full_name}</strong>
                              <span className="ml-2 text-muted-foreground">
                                {s.user_id} · {s.email}
                              </span>
                            </div>
                          ))}
                      {classId &&
                        !classStudents.isPending &&
                        !candidates.length && (
                          <p className="p-3 text-sm text-muted-foreground">
                            Không có sinh viên mới.
                          </p>
                        )}
                    </div>
                  </>
                ) : (
                  <Input
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    placeholder="MSSV"
                  />
                )}
              </div>
              <div className="flex justify-end">
                <Button
                  disabled={
                    adding || mode === "class"
                      ? !classId ||
                        classStudents.isPending ||
                        !candidates.length
                      : !studentId.trim()
                  }
                  onClick={() => void add()}
                  className="bg-[#34227a] text-white"
                >
                  {adding ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />} {adding ? "Đang thêm..." : "Thêm"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full min-w-[780px] text-sm">
          <thead className="bg-indigo-50 text-left text-xs font-semibold">
            <tr>
              <th className="px-4 py-3">STT</th>
              <th className="px-4 py-3">MSSV</th>
              <th className="px-4 py-3">HỌ TÊN</th>
              <th className="px-4 py-3">TIẾN ĐỘ</th>
              <th className="px-4 py-3 text-right">THAO TÁC</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((student, index) => (
              <tr key={student.student_id} className="border-t">
                <td className="px-4 py-3">{index + 1}</td>
                <td className="px-4 py-3 font-semibold">
                  {student.student_id}
                </td>
                <td className="px-4 py-3">
                  <div className="font-semibold">{student.full_name}</div>
                  <div className="text-xs text-muted-foreground">
                    {student.email}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-32 rounded-full bg-indigo-100">
                      <div
                        className="h-full rounded-full bg-indigo-800"
                        style={{ width: `${student.progress_percent}%` }}
                      />
                    </div>
                    <span className="text-xs">{student.progress_percent}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => void remove(student)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <AlertDialog open={Boolean(pendingDelete)} onOpenChange={(next) => { if (!next && !deleting) setPendingDelete(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>Xác nhận xóa sinh viên</AlertDialogTitle><AlertDialogDescription>Bạn có chắc muốn xóa sinh viên <strong>{pendingDelete?.full_name}</strong> ({pendingDelete?.student_id}) khỏi lớp này không? Thao tác này không thể hoàn tác.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel disabled={deleting}>Hủy</AlertDialogCancel><AlertDialogAction disabled={deleting} onClick={(event) => { event.preventDefault(); void confirmRemove(); }}>{deleting && <Loader2 className="size-4 animate-spin" />} {deleting ? "Đang xóa..." : "Xác nhận xóa"}</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
