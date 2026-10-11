"use client";

import { useRef, useState } from "react";
import { CheckCircle2, FileSpreadsheet, Loader2, Upload, XCircle } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/error";
import { importStudents } from "@/lib/api/endpoints/admin";
import type { ImportStudentsResponse } from "@/lib/api/types";

const MAX_FILE_BYTES = 5 * 1024 * 1024;

export function StudentImport() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportStudentsResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function chooseFile(next: File | undefined) {
    if (!next || isSubmitting) return;
    if (!/\.(xls|xlsx)$/i.test(next.name)) {
      toast.error("Vui lòng chọn file Excel định dạng .xls hoặc .xlsx.");
      return;
    }
    if (next.size > MAX_FILE_BYTES) {
      toast.error("File Excel không được vượt quá 5 MB.");
      return;
    }
    if (next.size === 0) {
      toast.error("File Excel đang trống.");
      return;
    }
    setFile(next);
    setResult(null);
  }

  async function upload() {
    if (!file || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const response = await importStudents(file);
      setResult(response);
      const summary = `Đã tạo ${response.created.length} tài khoản, bỏ qua ${response.skipped.length}, lỗi ${response.errors.length} dòng.`;
      if (response.errors.length > 0) {
        toast.warning(summary);
      } else if (response.created.length > 0) {
        toast.success(summary);
      } else {
        toast.info(summary);
      }
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Không thể nhập danh sách sinh viên.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-indigo-700">Quản lý tài khoản / Nhập danh sách từ Excel</p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          Nhập danh sách Sinh viên từ Excel
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Tải lên danh sách lớp học phần để kiểm tra dữ liệu và cấp tài khoản sinh viên hàng loạt.
        </p>
      </div>

      <section className="rounded-2xl bg-gradient-to-r from-[#352078] via-[#4a2d9a] to-[#5d4ab0] p-6 text-white shadow-lg">
        <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-medium">
          Use-case: Cấp phát tài khoản hàng loạt
        </span>
        <h2 className="mt-4 text-2xl font-bold">Nhập danh sách Sinh viên từ Excel</h2>
        <p className="mt-1 max-w-3xl text-sm text-purple-100">
          Hệ thống kiểm tra từng dòng, tự sinh email và mật khẩu tạm từ mã sinh viên, đồng thời tạo
          lớp hành chính chưa có.
        </p>
      </section>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(18rem,0.8fr)]">
        <section className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900">
          <h2 className="font-bold">1. Tải lên danh sách lớp học phần</h2>
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => inputRef.current?.click()}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              chooseFile(event.dataTransfer.files[0]);
            }}
            className="mt-5 flex min-h-32 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-purple-200 bg-purple-50/40 px-4 text-center transition hover:border-purple-400 hover:bg-purple-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Upload className="size-8 text-indigo-700" />
            <span className="mt-2 font-semibold text-slate-700">
              Kéo thả file .xls/.xlsx hoặc bấm để chọn file
            </span>
            <span className="mt-1 text-xs text-slate-500">
              Tối đa 5 MB và 500 sinh viên mỗi lần nhập
            </span>
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".xls,.xlsx"
            className="hidden"
            aria-label="Chọn file Excel danh sách sinh viên"
            onChange={(event) => {
              chooseFile(event.target.files?.[0]);
              event.target.value = "";
            }}
          />
          {file && (
            <div className="mt-4 flex items-center gap-3 rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
              <FileSpreadsheet className="size-7 text-emerald-600" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold">{file.name}</p>
                <p className="text-xs text-slate-500">
                  {(file.size / 1024).toFixed(1)} KB · Đã chọn dữ liệu
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                disabled={isSubmitting}
                onClick={() => {
                  setFile(null);
                  setResult(null);
                }}
                aria-label="Bỏ file"
              >
                <XCircle className="size-4 text-slate-400" />
              </Button>
            </div>
          )}
          <div className="mt-5 flex justify-end">
            <Button
              disabled={!file || isSubmitting || result !== null}
              onClick={() => void upload()}
              className="bg-[#352078] hover:bg-[#29175f]"
            >
              {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
              {isSubmitting ? "Đang tạo tài khoản..." : result ? "Đã nhập file" : "Tải lên và tạo tài khoản"}
            </Button>
          </div>
        </section>

        <section className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900">
          <h2 className="font-bold">2. Yêu cầu đối với file Excel</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
            <li className="flex gap-2">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />
              Dùng mẫu danh sách lớp học phần với các cột STT, Mã sinh viên (MSSV), Họ và tên, Lớp.
            </li>
            <li className="flex gap-2">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />
              Hàng tiêu đề phải nằm trong 20 hàng đầu của mỗi sheet cần nhập.
            </li>
            <li className="flex gap-2">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />
              Mã lớp theo dạng &lt;hệ&gt;.&lt;khóa&gt;.&lt;ngành&gt;, ví dụ CQ.67.CNTT.
            </li>
            <li className="flex gap-2">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />
              Email có dạng MSSV@st.utc2.edu.vn; mật khẩu tạm là MSSV và phải đổi sau lần đăng nhập đầu.
            </li>
          </ul>
        </section>
      </div>

      {result && (
        <section className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-bold">3. Kết quả nhập danh sách sinh viên</h2>
              <p className="text-sm text-slate-500">File: {file?.name}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
                Đã tạo {result.created.length}
              </span>
              <span className="rounded-full bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-700">
                Bỏ qua {result.skipped.length}
              </span>
              <span className="rounded-full bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">
                Lỗi {result.errors.length}
              </span>
            </div>
          </div>

          {result.created.length > 0 && (
            <div className="mt-5">
              <h3 className="mb-2 font-semibold">Tài khoản đã tạo</h3>
              <p className="mb-3 text-sm text-slate-500">
                Hãy lưu lại mật khẩu tạm trước khi rời trang.
              </p>
              <div className="overflow-x-auto rounded-xl border">
                <table className="w-full min-w-[760px] text-sm">
                  <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500 dark:bg-slate-800">
                    <tr>
                      <th className="px-4 py-3">MSSV</th>
                      <th className="px-4 py-3">Họ và tên</th>
                      <th className="px-4 py-3">Lớp</th>
                      <th className="px-4 py-3">Email</th>
                      <th className="px-4 py-3">Mật khẩu tạm</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.created.map((row) => (
                      <tr key={row.user_id} className="border-t">
                        <td className="px-4 py-3 font-medium">{row.user_id}</td>
                        <td className="px-4 py-3">{row.full_name}</td>
                        <td className="px-4 py-3">{row.class_id}</td>
                        <td className="px-4 py-3">{row.email}</td>
                        <td className="px-4 py-3">
                          <code className="rounded bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">
                            {row.temporary_password}
                          </code>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {result.skipped.length > 0 && (
            <div className="mt-5 overflow-x-auto rounded-xl border border-amber-200">
              <div className="bg-amber-50 px-4 py-3 font-semibold text-amber-700">
                Đã bỏ qua {result.skipped.length} sinh viên
              </div>
              <table className="w-full min-w-[650px] text-sm">
                <thead className="bg-amber-50/50 text-left text-xs uppercase text-amber-700">
                  <tr>
                    <th className="px-4 py-3">Sheet</th>
                    <th className="px-4 py-3">Dòng Excel</th>
                    <th className="px-4 py-3">MSSV</th>
                    <th className="px-4 py-3">Lý do</th>
                  </tr>
                </thead>
                <tbody>
                  {result.skipped.map((row) => (
                    <tr key={`${row.sheet}-${row.row}-${row.user_id}`} className="border-t border-amber-100">
                      <td className="px-4 py-3">{row.sheet}</td>
                      <td className="px-4 py-3">{row.row}</td>
                      <td className="px-4 py-3">{row.user_id}</td>
                      <td className="px-4 py-3 text-amber-700">{row.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.errors.length > 0 && (
            <div className="mt-5 overflow-x-auto rounded-xl border border-rose-200">
              <div className="flex items-center gap-2 bg-rose-50 px-4 py-3 font-semibold text-rose-700">
                <XCircle className="size-4" />
                Chi tiết {result.errors.length} dòng lỗi
              </div>
              <table className="w-full min-w-[650px] text-sm">
                <thead className="bg-rose-50/50 text-left text-xs uppercase text-rose-700">
                  <tr>
                    <th className="px-4 py-3">Sheet</th>
                    <th className="px-4 py-3">Dòng Excel</th>
                    <th className="px-4 py-3">MSSV</th>
                    <th className="px-4 py-3">Lý do</th>
                  </tr>
                </thead>
                <tbody>
                  {result.errors.map((row) => (
                    <tr key={`${row.sheet}-${row.row}-${row.user_id ?? ""}`} className="border-t border-rose-100">
                      <td className="px-4 py-3">{row.sheet}</td>
                      <td className="px-4 py-3">{row.row}</td>
                      <td className="px-4 py-3">{row.user_id || "—"}</td>
                      <td className="px-4 py-3 text-rose-700">{row.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
