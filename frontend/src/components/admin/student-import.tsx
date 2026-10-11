"use client";

import { useRef, useState } from "react";
import { CheckCircle2, Download, FileSpreadsheet, Loader2, Upload, XCircle } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/error";
import { importStudents } from "@/lib/api/endpoints/admin";
import type { ImportStudentsResponse } from "@/lib/api/types";

export function StudentImport() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportStudentsResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function chooseFile(next: File | undefined) {
    if (!next) return;
    if (!next.name.toLowerCase().endsWith(".xlsx")) {
      toast.error("Vui lòng chọn file Excel định dạng .xlsx.");
      return;
    }
    setFile(next);
    setResult(null);
  }

  async function upload() {
    if (!file) return;
    setIsSubmitting(true);
    try {
      const response = await importStudents(file);
      setResult(response);
      toast.success(`Đã xử lý ${response.created.length} dòng hợp lệ.`);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Không thể xử lý file Excel.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return <div className="space-y-6"><div><p className="text-sm font-medium text-indigo-700">Quản lý tài khoản / Nhập danh sách từ Excel</p><h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Nhập danh sách Sinh viên từ Excel</h1><p className="mt-1 text-sm text-slate-500">Tải lên file .xlsx để hệ thống kiểm tra dữ liệu và cấp tài khoản hàng loạt.</p></div><section className="rounded-2xl bg-gradient-to-r from-[#352078] via-[#4a2d9a] to-[#5d4ab0] p-6 text-white shadow-lg"><span className="rounded-full bg-white/15 px-3 py-1 text-xs font-medium">Use-case: Cấp phát tài khoản hàng loạt</span><h2 className="mt-4 text-2xl font-bold">Nhập danh sách Sinh viên từ Excel</h2><p className="mt-1 max-w-3xl text-sm text-purple-100">Hệ thống tự động kiểm tra định dạng, email trùng lặp, mã lớp và tạo mật khẩu tạm theo ngày sinh.</p></section><div className="grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(18rem,0.8fr)]"><section className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900"><div className="flex items-center justify-between gap-3"><h2 className="font-bold">1. Tải lên file dữ liệu sinh viên (.xlsx)</h2><Button variant="outline" size="sm" onClick={() => toast.info("Mẫu Excel sẽ được bổ sung khi backend chốt cấu trúc tải xuống.")}><Download className="size-4" />Tải file Excel mẫu</Button></div><button type="button" onClick={() => inputRef.current?.click()} className="mt-5 flex min-h-32 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-purple-200 bg-purple-50/40 px-4 text-center transition hover:border-purple-400 hover:bg-purple-50"><Upload className="size-8 text-indigo-700" /><span className="mt-2 font-semibold text-slate-700">Kéo thả file danh sách sinh viên (.xlsx) hoặc bấm Chọn file</span><span className="mt-1 text-xs text-slate-400">Hỗ trợ các định dạng tiêu chuẩn, tối đa 500 dòng</span></button><input ref={inputRef} type="file" accept=".xlsx" className="hidden" onChange={(e) => chooseFile(e.target.files?.[0])} />{file && <div className="mt-4 flex items-center gap-3 rounded-xl bg-slate-50 p-3"><FileSpreadsheet className="size-7 text-emerald-600" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{file.name}</p><p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB · Đã chọn dữ liệu</p></div><Button variant="ghost" size="icon" onClick={() => { setFile(null); setResult(null); }} aria-label="Bỏ file"><XCircle className="size-4 text-slate-400" /></Button></div>}<div className="mt-5 flex justify-end"><Button disabled={!file || isSubmitting} onClick={() => void upload()} className="bg-[#352078] hover:bg-[#29175f]">{isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}{isSubmitting ? "Đang xử lý..." : "Tải lên và kiểm tra"}</Button></div></section><section className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900"><h2 className="font-bold">2. Quy định xác thực file mẫu</h2><ul className="mt-4 space-y-3 text-sm text-slate-600"><li className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />Các cột bắt buộc: user_id, họ tên, ngày sinh, email, mã lớp.</li><li className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />Email phải đúng định dạng và chưa tồn tại.</li><li className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />Mã lớp phải tồn tại trong hệ thống.</li><li className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />Mật khẩu tạm sinh từ ngày sinh và bắt buộc đổi lần đầu.</li></ul></section></div>{result && <section className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-bold">3. Kết quả phân tích và kiểm tra hợp lệ dữ liệu</h2><p className="text-sm text-slate-500">File: {file?.name}</p></div><div className="flex gap-2"><span className="rounded-full bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">Tài khoản hợp lệ {result.created.length}</span><span className="rounded-full bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">Dòng lỗi {result.errors.length}</span></div></div><div className="mt-5 overflow-x-auto rounded-xl border"><table className="w-full min-w-[700px] text-sm"><thead className="bg-slate-50 text-left text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">STT</th><th className="px-4 py-3">Họ và tên</th><th className="px-4 py-3">Email</th><th className="px-4 py-3">Mật khẩu tạm</th><th className="px-4 py-3">Trạng thái</th></tr></thead><tbody>{result.created.map((row, index) => <tr key={row.user_id} className="border-t"><td className="px-4 py-3 text-slate-400">{index + 1}</td><td className="px-4 py-3 font-semibold">{row.full_name}</td><td className="px-4 py-3">{row.email}</td><td className="px-4 py-3"><code className="rounded bg-slate-100 px-2 py-1 text-xs">{row.temporary_password}</code></td><td className="px-4 py-3 text-emerald-600">Hợp lệ</td></tr>)}</tbody></table></div>{result.errors.length > 0 && <div className="mt-5 overflow-x-auto rounded-xl border border-rose-200"><div className="flex items-center gap-2 bg-rose-50 px-4 py-3 font-semibold text-rose-700"><XCircle className="size-4" />Chi tiết {result.errors.length} dòng dữ liệu lỗi</div><table className="w-full min-w-[650px] text-sm"><thead className="bg-rose-50/50 text-left text-xs uppercase text-rose-700"><tr><th className="px-4 py-3">Dòng Excel</th><th className="px-4 py-3">Email</th><th className="px-4 py-3">Lý do</th></tr></thead><tbody>{result.errors.map((row) => <tr key={`${row.row}-${row.email}`} className="border-t border-rose-100"><td className="px-4 py-3 font-semibold">Dòng {row.row}</td><td className="px-4 py-3">{row.email || "—"}</td><td className="px-4 py-3 text-rose-700">{row.reason}</td></tr>)}</tbody></table></div>}</section>}</div>;
}
