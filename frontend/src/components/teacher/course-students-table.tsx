"use client";

import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CircleUserRound, Download, History, Plus, Search, Trash2, UserPlus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { addClassToCourse, addStudentToCourse, deleteStudentFromCourse } from "@/lib/api/endpoints/courses";
import { useClassStudents, useClasses } from "@/lib/hooks/use-courses";
import type { CourseStudent } from "@/lib/types/course";

interface CourseStudentsTableProps { students: CourseStudent[]; courseId: string; onChanged?: () => void; }
const initials = (name: string) => name.split(" ").map((part) => part[0]).join("").slice(-2);

export function CourseStudentsTable({ students, courseId, onChanged }: CourseStudentsTableProps) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"class" | "individual">("class");
  const [removedIds, setRemovedIds] = useState<string[]>([]);
  const [tableQuery, setTableQuery] = useState("");
  const [studentId, setStudentId] = useState("");
  const [selectedClass, setSelectedClass] = useState("");
  const [historyStudent, setHistoryStudent] = useState<CourseStudent | null>(null);
  const classes = useClasses(open && mode === "class");
  const classStudents = useClassStudents(selectedClass, open && mode === "class");
  const enrolledIds = useMemo(() => new Set(students.map((student) => student.student_id)), [students]);
  const classCandidates = useMemo(() => (classStudents.data ?? []).filter((student) => !enrolledIds.has(student.user_id)), [classStudents.data, enrolledIds]);
  const rows = useMemo(() => students.filter((student) => !removedIds.includes(student.student_id)), [students, removedIds]);
  const filteredRows = useMemo(() => rows.filter((student) => `${student.student_id} ${student.full_name} ${student.email}`.toLowerCase().includes(tableQuery.toLowerCase())), [rows, tableQuery]);

  function closeDialog() {
    setOpen(false);
    setMode("class");
    setStudentId("");
    setSelectedClass("");
  }

  async function refreshData() {
    await queryClient.invalidateQueries({ queryKey: ["courses", "enrollments", courseId] });
    await queryClient.invalidateQueries({ queryKey: ["courses", "detail", courseId] });
    onChanged?.();
  }

  async function removeStudent(student: CourseStudent) {
    if (!window.confirm(`Xóa ${student.full_name} khỏi lớp học phần?`)) return;
    try {
      await deleteStudentFromCourse(courseId, student.student_id);
      setRemovedIds((current) => [...current, student.student_id]);
      await refreshData();
      toast.success("Đã xóa sinh viên khỏi lớp học phần.");
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể xóa sinh viên."); }
  }

  async function addStudents() {
    if (mode === "class" && !selectedClass) return;
    if (mode === "individual" && !studentId.trim()) return;
    try {
      if (mode === "class") {
        const result = await addClassToCourse(courseId, selectedClass);
        await refreshData();
        toast.success(`Đã thêm ${result.added_count} sinh viên; bỏ qua ${result.skipped_count} sinh viên đã có.`);
      } else {
        await addStudentToCourse(courseId, studentId.trim());
        await refreshData();
        toast.success("Đã thêm sinh viên vào lớp học phần.");
      }
      closeDialog();
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể thêm sinh viên."); }
  }

  return <section className="space-y-4 rounded-xl bg-card p-4 shadow-sm">
    <div className="flex flex-wrap items-center justify-between gap-3"><div className="relative w-full max-w-sm"><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={tableQuery} onChange={(event) => setTableQuery(event.target.value)} className="h-9 border-0 bg-slate-50 pl-9 shadow-none" placeholder="Nhập MSSV, họ tên, email cần tìm..." /></div><div className="flex gap-2"><Button variant="outline" className="h-9 border-indigo-100 bg-indigo-50 text-indigo-800"><Download className="size-4" /> Xuất Excel (.xlsx)</Button><Dialog open={open} onOpenChange={setOpen}><DialogTrigger render={<Button className="h-9 bg-[#34227a] text-white hover:bg-[#28195f]"><UserPlus className="size-4" /> Thêm sinh viên</Button>} /><DialogContent className="max-h-[calc(100vh-2rem)] max-w-[760px] overflow-y-auto rounded-2xl p-0"><DialogHeader className="bg-indigo-50 px-6 py-5 text-left"><DialogTitle>Thêm sinh viên vào lớp học phần</DialogTitle><DialogDescription>Chọn cả lớp để thêm toàn bộ sinh viên chưa có trong khóa học.</DialogDescription></DialogHeader><div className="space-y-5 p-6"><div className="grid grid-cols-2 rounded-md bg-indigo-50 p-1 text-center text-sm font-semibold"><button type="button" onClick={() => setMode("class")} className={mode === "class" ? "rounded bg-card py-2 text-indigo-800 shadow-sm" : "py-2 text-muted-foreground"}>Theo lớp hành chính</button><button type="button" onClick={() => setMode("individual")} className={mode === "individual" ? "rounded bg-card py-2 text-indigo-800 shadow-sm" : "py-2 text-muted-foreground"}>Nhập MSSV</button></div>{mode === "class" ? <div className="space-y-3 rounded-lg bg-indigo-50 p-4"><label className="text-xs font-semibold">Lớp hành chính<select value={selectedClass} onChange={(event) => setSelectedClass(event.target.value)} className="mt-2 h-9 w-full rounded-md border bg-card px-3 text-sm"><option value="">Chọn lớp</option>{(classes.data ?? []).map((item) => <option key={item.class_id} value={item.class_id}>{item.class_id} — {item.department}</option>)}</select></label>{classes.error && <p className="text-xs text-red-600">Không tải được danh sách lớp.</p>}{classStudents.isPending && selectedClass && <p className="text-xs text-muted-foreground">Đang tải sinh viên trong lớp...</p>}{selectedClass && !classStudents.isPending && <p className="text-xs font-medium text-indigo-800">Đã chọn tất cả {classCandidates.length} sinh viên chưa có trong khóa học.</p>}{classStudents.error && <p className="text-xs text-red-600">Không tải được sinh viên của lớp.</p>}</div> : <div className="space-y-3 rounded-lg bg-indigo-50 p-4"><label className="text-sm font-semibold">Mã số sinh viên<Input value={studentId} onChange={(event) => setStudentId(event.target.value)} className="mt-2 h-10 bg-card" placeholder="Ví dụ: 2151129901" autoFocus /></label></div>}<div className="max-h-64 space-y-1 overflow-auto">{mode === "class" && classCandidates.map((student) => <div key={student.user_id} className="flex items-center gap-3 rounded bg-card p-2"><input type="checkbox" checked readOnly className="size-4 accent-indigo-700" /><span className="flex size-7 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-bold text-indigo-800">{initials(student.full_name)}</span><span className="text-xs"><strong className="block">{student.full_name}</strong><span className="text-muted-foreground">{student.user_id} · {student.email}</span></span></div>)}{mode === "class" && selectedClass && !classStudents.isPending && !classCandidates.length && <p className="py-5 text-center text-xs text-muted-foreground">Không có sinh viên mới trong lớp này.</p>}</div><div className="flex justify-end gap-2"><Button variant="outline" onClick={closeDialog}>Hủy bỏ</Button><Button disabled={mode === "class" ? !selectedClass || classStudents.isPending || !classCandidates.length : !studentId.trim()} onClick={() => void addStudents()} className="bg-[#34227a] text-white"><Plus className="size-4" /> {mode === "class" ? "Thêm tất cả" : "Thêm sinh viên"}</Button></div></div></DialogContent></Dialog></div></div>
    <div className="overflow-x-auto rounded-lg border"><table className="w-full min-w-[900px] text-sm"><thead className="bg-indigo-50 text-left text-xs font-semibold uppercase text-indigo-950"><tr><th className="px-4 py-3">STT</th><th className="px-4 py-3">MSSV</th><th className="px-4 py-3">HỌ TÊN</th><th className="px-4 py-3">TIẾN ĐỘ BÀI NỘP</th><th className="px-4 py-3">TIẾN ĐỘ</th><th className="px-4 py-3 text-right">THAO TÁC</th></tr></thead><tbody>{filteredRows.map((student, index) => <tr key={student.enrollment_id || student.student_id} className="border-t transition-colors hover:bg-indigo-50/40"><td className="px-4 py-4 text-muted-foreground">{String(index + 1).padStart(2, "0")}</td><td className="px-4 py-4 font-semibold text-indigo-800">{student.student_id}</td><td className="px-4 py-4"><div className="flex items-center gap-3"><span className="flex size-9 items-center justify-center rounded-full bg-indigo-100 text-indigo-800"><CircleUserRound className="size-5" /></span><div><p className="font-semibold">{student.full_name}</p><p className="text-xs text-muted-foreground">{student.email}</p></div></div></td><td className="px-4 py-4">{student.submitted_lessons}/{student.total_lessons} bài AC</td><td className="px-4 py-4"><div className="flex items-center gap-2"><div className="h-2 w-32 rounded-full bg-indigo-100"><div className="h-full rounded-full bg-indigo-800" style={{ width: `${student.progress_percent}%` }} /></div><span className="text-xs text-muted-foreground">{student.progress_percent}%</span></div></td><td className="px-4 py-4"><div className="flex justify-end gap-1"><Button variant="ghost" size="icon" title="Xem lịch sử nộp bài" onClick={() => setHistoryStudent(student)}><History className="size-4" /></Button><Button variant="ghost" size="icon" title="Xóa sinh viên" className="text-slate-500 hover:text-red-600" onClick={() => void removeStudent(student)}><Trash2 className="size-4" /></Button></div></td></tr>)}</tbody></table></div>
    <Dialog open={historyStudent !== null} onOpenChange={(value) => !value && setHistoryStudent(null)}><DialogContent className="max-w-[640px]"><DialogHeader><DialogTitle>Lịch sử nộp bài</DialogTitle><DialogDescription>{historyStudent?.full_name} · {historyStudent?.student_id}</DialogDescription></DialogHeader><div className="rounded-lg border p-4 text-sm text-amber-800">Backend hiện chưa trả lịch sử Submission trong API danh sách enrollment.</div></DialogContent></Dialog>
  </section>;
}
