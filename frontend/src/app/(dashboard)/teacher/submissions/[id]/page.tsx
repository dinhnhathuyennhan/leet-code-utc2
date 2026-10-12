"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Code2,
  Save,
  XCircle,
} from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function SubmissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  useBreadcrumbLabel(`Chấm bài #${id}`);

  const [score, setScore] = useState("8.0");
  const [feedback, setFeedback] = useState("Thuật toán tối ưu, cần lưu ý điều kiện biên mảng rỗng.");
  const [saved, setSaved] = useState(false);

  const mockCode = `import java.util.Scanner;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (!sc.hasNextInt()) return;
        int n = sc.nextInt();
        int sum = 0;
        for (int i = 0; i < n; i++) {
            int val = sc.nextInt();
            if (val > 0 && val % 2 == 0) {
                sum += val;
            }
        }
        System.out.println(sum);
    }
}`;

  return (
    <div className="space-y-6">
      {/* ─── Top Header ────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button asChild variant="outline" size="sm" className="gap-1.5 border-slate-300">
            <Link href="/teacher">
              <ArrowLeft className="size-4" /> Quay lại
            </Link>
          </Button>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-2xl">
              Chấm bài & Xử lý khiếu nại #{id}
            </h1>
            <p className="text-xs text-muted-foreground">
              Bài tập: ARR_01 - Tổng các phần tử trong mảng 1 chiều · Lớp JAVA01
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => setSaved(true)}
            className="h-10 bg-[#2f226b] gap-2 font-semibold text-white shadow-sm hover:bg-[#251b56]"
          >
            <Save className="size-4" /> {saved ? "Đã lưu kết quả" : "Lưu điểm & Gửi phản hồi"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
        {/* ─── Left column: Code viewer & Test cases ───────────────────────── */}
        <div className="space-y-6">
          {/* Sinh viên info card */}
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-4 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="flex size-10 items-center justify-center rounded-full bg-indigo-100 font-bold text-indigo-900 dark:bg-indigo-500/20 dark:text-indigo-200">
                A
              </span>
              <div>
                <p className="font-semibold text-slate-900 dark:text-slate-100">Nguyễn Văn An</p>
                <p className="text-xs text-muted-foreground">MSSV: 2151129812 · Lớp JAVA01</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs">
              <span className="flex items-center gap-1 rounded-md bg-amber-50 px-2.5 py-1 font-medium text-amber-800 dark:bg-amber-500/20 dark:text-amber-300">
                <Clock className="size-3.5" /> Nộp trễ 45 phút
              </span>
              <span className="rounded-md bg-red-100 px-2.5 py-1 font-semibold text-red-700 dark:bg-red-500/20 dark:text-red-300">
                WA: 8/10 Test Passed
              </span>
            </div>
          </div>

          {/* Source code viewer */}
          <div className="overflow-hidden rounded-xl border bg-slate-950 text-slate-100 shadow-md">
            <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/80 px-4 py-2.5">
              <div className="flex items-center gap-2">
                <Code2 className="size-4 text-sky-400" />
                <span className="font-mono text-xs text-slate-300">Solution.java (JDK 17)</span>
              </div>
              <span className="text-xs text-slate-400">Thời gian chạy: 0.12s · Bộ nhớ: 32MB</span>
            </div>
            <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-slate-200">
              <code>{mockCode}</code>
            </pre>
          </div>

          {/* Test cases execution status */}
          <div className="rounded-xl border bg-card p-5 shadow-xs">
            <h3 className="mb-3 text-sm font-bold text-slate-900 dark:text-slate-100">
              Kết quả chi tiết các Test Cases (8/10 Đúng)
            </h3>
            <div className="grid gap-2 sm:grid-cols-2">
              {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
                <div key={num} className="flex items-center justify-between rounded-lg border bg-muted/30 px-3 py-2 text-xs">
                  <span className="font-medium">Test #{num} (Bình thường)</span>
                  <span className="flex items-center gap-1 font-semibold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="size-3.5" /> 100/100 ms
                  </span>
                </div>
              ))}
              {[9, 10].map((num) => (
                <div key={num} className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50/50 px-3 py-2 text-xs dark:bg-red-500/10">
                  <span className="font-medium text-red-900 dark:text-red-200">Test #{num} (Mảng số âm)</span>
                  <span className="flex items-center gap-1 font-semibold text-red-600 dark:text-red-400">
                    <XCircle className="size-3.5" /> Sai kết quả (WA)
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ─── Right column: Grading panel ─────────────────────────────────── */}
        <div className="space-y-6">
          <div className="space-y-4 rounded-xl border bg-card p-5 shadow-xs">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Đánh giá & Chấm điểm
            </h3>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Điểm số (Thang 10)
              </label>
              <Input
                type="number"
                step="0.5"
                max="10"
                min="0"
                value={score}
                onChange={(e) => setScore(e.target.value)}
                className="mt-1 h-11 text-lg font-bold"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Lý do & Đơn xin cứu xét của sinh viên
              </label>
              <div className="mt-1 rounded-lg border bg-amber-50/70 p-3 text-xs text-amber-900 dark:bg-amber-500/10 dark:text-amber-200">
                <p className="font-semibold">Lý do nộp trễ:</p>
                <p className="mt-0.5">
                  &quot;Em bị sự cố mất điện cục bộ tại phòng trọ lúc 23h30 nên xin nộp bù sau khi có điện trở lại. Kính mong thầy hỗ trợ chấm bài giúp em ạ!&quot;
                </p>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Nhận xét của giảng viên
              </label>
              <Textarea
                rows={4}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="mt-1 text-sm"
                placeholder="Nhập nhận xét gửi cho sinh viên..."
              />
            </div>

            <Button
              onClick={() => setSaved(true)}
              className="w-full h-11 bg-[#2f226b] font-semibold text-white shadow-sm hover:bg-[#251b56]"
            >
              <Save className="size-4 mr-2" /> {saved ? "Đã cập nhật điểm" : "Xác nhận điểm & Chấp nhận"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
