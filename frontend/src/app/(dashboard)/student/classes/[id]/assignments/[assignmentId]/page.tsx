"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Check,
  ChevronRight,
  Clock,
  Copy,
  Lock,
  Play,
  Send,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { cn } from "@/lib/utils";

/**
 * Coding Workspace — "Modern Minimal + Developer Tool".
 *
 * Layout (theo Figma):
 *  - Topbar: back link + breadcrumb + ngôn ngữ + nút Chạy thử / Nộp bài
 *  - Cột trái (42%): đề bài (mục tiêu, I/O, ví dụ, ràng buộc)
 *  - Cột phải (58%): editor code (Monaco-style) + Judge Console
 *
 * Hiện đang dùng mock data + editor giả lập (textarea) — người khác đang
 * code phần backend judge. Khi họ xong, thay phần <MockCodeEditor /> bằng
 * Monaco thật.
 *
 * Bảng màu thương hiệu:
 *  - Nền: #F6F7FA, bề mặt: #FFFFFF
 *  - Tím đại học: #352078
 *  - Vàng: #F5CD16
 */

const BRAND = {
  primary: "#352078",
  primaryHover: "#2a1a60",
  yellow: "#F5CD16",
  surface: "#FFFFFF",
  background: "#F6F7FA",
};

interface TestcaseResult {
  id: number;
  label: string;
  isSample: boolean;
  locked: boolean; // test ẩn có ổ khóa
  status: "passed" | "failed" | "pending" | "hidden";
  runtimeMs: number | null;
  output: string | null;
  expected: string | null;
}

interface AssignmentFull {
  id: string;
  code: string;
  title: string;
  difficulty: "Easy" | "Medium" | "Hard";
  deadline: string;
  description: string;
  inputFormat: string;
  outputFormat: string;
  sampleInput: string;
  sampleOutput: string;
  constraints: string;
  hints: string[];
  starterCode: string;
  testcases: TestcaseResult[];
}

const MOCK_ASSIGNMENT: AssignmentFull = {
  id: "2",
  code: "EX02",
  title: "Số chẵn lẻ",
  difficulty: "Easy",
  deadline: "2026-09-18T23:59:00",
  description: `Cho một số nguyên **n**, hãy in ra:

- **"Even"** nếu *n* chia hết cho 2
- **"Odd"** nếu *n* không chia hết cho 2`,
  inputFormat: `Một số nguyên *n* duy nhất trên một dòng.`,
  outputFormat: `In ra \`"Even"\` hoặc \`"Odd"\` tương ứng.`,
  sampleInput: `4`,
  sampleOutput: `Even`,
  constraints: `| Giá trị              | Phạm vi        |
| -------------------- | -------------- |
| n                    | -10^9 ≤ n ≤ 10^9 |
| Time limit           | 1 giây          |
| Memory limit         | 256 MB          |`,
  hints: [
    "Sử dụng toán tử `%` để lấy phần dư khi chia cho 2.",
    "Không cần xử lý ngoại lệ đầu vào — đề bài đảm bảo input hợp lệ.",
  ],
  starterCode: `import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        long n = sc.nextLong();

        // TODO: In ra "Even" nếu n chia hết cho 2, ngược lại in ra "Odd"
    }
}
`,
  testcases: [
    {
      id: 1,
      label: "Sample #1",
      isSample: true,
      locked: false,
      status: "passed",
      runtimeMs: 12,
      output: "Even",
      expected: "Even",
    },
    {
      id: 2,
      label: "Sample #2",
      isSample: true,
      locked: false,
      status: "passed",
      runtimeMs: 14,
      output: "Odd",
      expected: "Odd",
    },
    {
      id: 3,
      label: "Hidden #1",
      isSample: false,
      locked: true,
      status: "pending",
      runtimeMs: null,
      output: null,
      expected: null,
    },
    {
      id: 4,
      label: "Hidden #2",
      isSample: false,
      locked: true,
      status: "pending",
      runtimeMs: null,
      output: null,
      expected: null,
    },
  ],
};

function CopyableBlock({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    if (typeof navigator === "undefined" || !navigator.clipboard) return;
    void navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-muted/40">
      <div className="flex items-center justify-between border-b border-border/60 bg-muted/60 px-3 py-1.5 text-xs font-medium text-muted-foreground">
        <span>{label}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium text-foreground/80 transition-colors hover:bg-background hover:text-foreground"
        >
          {copied ? (
            <>
              <Check className="size-3" />
              Đã sao chép
            </>
          ) : (
            <>
              <Copy className="size-3" />
              Sao chép
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto px-3 py-2.5 text-sm leading-relaxed">
        <code>{value}</code>
      </pre>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-2.5">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      <div className="space-y-2.5 text-[15px] leading-relaxed text-foreground">
        {children}
      </div>
    </section>
  );
}

function CodeEditorMock({
  value,
  onChange,
  language,
}: {
  value: string;
  onChange: (v: string) => void;
  language: string;
}) {
  // Editor giả lập — syntax highlight rất đơn giản.
  // Khi người khác code xong Monaco, thay bằng <MonacoEditor />.
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-border bg-[#1e1e1e] text-sm">
      <div className="flex items-center justify-between border-b border-white/10 bg-[#252526] px-4 py-1.5 text-xs">
        <div className="flex items-center gap-3">
          <span className="rounded bg-white/5 px-2 py-0.5 font-mono text-white/80">
            Main.{language === "java" ? "java" : language}
          </span>
          <span className="text-white/40">UTF-8</span>
          <span className="text-white/40">LF</span>
        </div>
        <span className="text-white/40">Line: {value.split("\n").length}</span>
      </div>
      <div className="flex flex-1 overflow-hidden">
        {/* Line numbers */}
        <div className="select-none border-r border-white/10 bg-[#1e1e1e] px-3 py-3 text-right font-mono text-[13px] leading-6 text-white/30">
          {value.split("\n").map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          spellCheck={false}
          className="flex-1 resize-none bg-[#1e1e1e] px-4 py-3 font-mono text-[13px] leading-6 text-white/90 outline-none"
        />
      </div>
    </div>
  );
}

function JudgeRow({ tc }: { tc: TestcaseResult }) {
  const statusStyles: Record<TestcaseResult["status"], { dot: string; text: string; label: string }> = {
    passed: { dot: "bg-emerald-500", text: "text-emerald-700", label: "Accepted" },
    failed: { dot: "bg-rose-500", text: "text-rose-700", label: "Wrong Answer" },
    pending: { dot: "bg-slate-400", text: "text-slate-600", label: "Pending" },
    hidden: { dot: "bg-slate-300", text: "text-slate-500", label: "Hidden" },
  };
  const s = statusStyles[tc.status];

  return (
    <div className="flex items-center gap-3 rounded-md border border-border bg-card px-3 py-2 text-sm">
      {tc.locked ? (
        <Lock className="size-4 text-muted-foreground" />
      ) : (
        <span className={cn("inline-block size-2.5 shrink-0 rounded-full", s.dot)} />
      )}
      <span className="font-medium text-foreground">{tc.label}</span>
      {tc.isSample && (
        <Badge variant="outline" className="border-border text-[10px] uppercase text-muted-foreground">
          Sample
        </Badge>
      )}
      <span className={cn("ml-auto text-xs font-medium", s.text)}>
        {tc.locked ? "Bảo mật" : s.label}
        {tc.runtimeMs !== null && ` · ${tc.runtimeMs}ms`}
      </span>
    </div>
  );
}

export default function StudentAssignmentDetailPage() {
  const { id, assignmentId } = useParams<{ id: string; assignmentId: string }>();
  const courseId = typeof id === "string" ? id : "";
  const aId = typeof assignmentId === "string" ? assignmentId : "";

  // TODO: thay bằng API call khi backend sẵn sàng
  const assignment = useMemo(() => MOCK_ASSIGNMENT, []);

  const [code, setCode] = useState(assignment.starterCode);
  const [results, setResults] = useState<TestcaseResult[]>(assignment.testcases);
  const [running, setRunning] = useState<"idle" | "running" | "submitting">("idle");

  useBreadcrumbLabel(assignment.title);

  useEffect(() => {
    console.log("[CodingWorkspace] mounted", { courseId, aId });
  }, [courseId, aId]);

  function handleRun() {
    if (running !== "idle") return;
    setRunning("running");
    // Giả lập chạy: 1.2s sau sẽ set passed cho sample + pending cho hidden
    window.setTimeout(() => {
      setResults((prev) =>
        prev.map((tc) =>
          tc.isSample
            ? { ...tc, status: "passed", runtimeMs: 11 + tc.id, output: tc.expected, expected: tc.expected }
            : { ...tc, status: "pending" },
        ),
      );
      setRunning("idle");
    }, 1200);
  }

  function handleSubmit() {
    if (running !== "idle") return;
    setRunning("submitting");
    // Giả lập nộp bài: 2s sau pass hết
    window.setTimeout(() => {
      setResults((prev) =>
        prev.map((tc, i) => ({
          ...tc,
          status: "passed",
          runtimeMs: 10 + i * 2,
          output: tc.expected,
          expected: tc.expected,
        })),
      );
      setRunning("idle");
    }, 2000);
  }

  return (
    <div
      className="-mx-6 -my-6 flex h-[calc(100vh-4rem)] flex-col bg-[#F6F7FA]"
      style={{ background: BRAND.background }}
    >
      {/* Topbar */}
      <header className="flex shrink-0 items-center gap-3 border-b border-border bg-card px-5 py-2.5">
        <Button
          variant="ghost"
          size="sm"
          render={
            <Link href={`/student/classes/${encodeURIComponent(courseId)}`}>
              <ArrowLeft className="size-4" />
              Quay lại lớp
            </Link>
          }
        />

        <nav className="flex min-w-0 items-center gap-1 text-sm text-muted-foreground">
          <span className="truncate font-mono text-xs">{courseId}</span>
          <ChevronRight className="size-3.5" />
          <span className="truncate font-medium text-foreground">{assignment.title}</span>
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <Badge
            variant="outline"
            className="border-[#352078]/20 bg-[#352078]/5 text-[#352078]"
          >
            Java
          </Badge>
          <span className="hidden items-center gap-1 text-xs text-muted-foreground sm:inline-flex">
            <Clock className="size-3.5" />
            Hạn nộp 18/09/2024 · 23:59
          </span>
        </div>
      </header>

      {/* Main: 2 columns */}
      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[42%_58%]">
        {/* LEFT: đề bài */}
        <aside className="min-h-0 overflow-y-auto border-r border-border bg-card">
          <div className="space-y-6 p-6">
            <header className="space-y-2 border-b border-border pb-4">
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                  Easy
                </span>
                <span className="font-mono text-xs text-muted-foreground">
                  {assignment.code}
                </span>
              </div>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                {assignment.title}
              </h1>
            </header>

            <Section title="Mục tiêu">
              <div
                className="prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{
                  __html: assignment.description
                    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
                    .replace(/\*(.+?)\*/g, "<em>$1</em>")
                    .replace(/`(.+?)`/g, '<code class="rounded bg-muted px-1 py-0.5 text-[13px]">$1</code>')
                    .split("\n")
                    .map((line) => `<p>${line}</p>`)
                    .join(""),
                }}
              />
            </Section>

            <Section title="Định dạng đầu vào">
              <p>{assignment.inputFormat}</p>
            </Section>

            <Section title="Định dạng đầu ra">
              <p>{assignment.outputFormat}</p>
            </Section>

            <Section title="Ví dụ mẫu">
              <div className="space-y-2.5">
                <CopyableBlock label="Input mẫu" value={assignment.sampleInput} />
                <CopyableBlock label="Output mẫu" value={assignment.sampleOutput} />
              </div>
            </Section>

            <Section title="Ràng buộc thực thi">
              <div
                className="overflow-hidden rounded-lg border border-border"
                dangerouslySetInnerHTML={{
                  __html: assignment.constraints
                    .split("\n")
                    .map((line) => line.trim())
                    .filter(Boolean)
                    .map((line, i, arr) => {
                      if (i === 0) return ""; // skip header "| ... |"
                      return `<div class="px-3 py-1.5 text-sm ${i < arr.length - 1 ? "border-b border-border" : ""}">${line}</div>`;
                    })
                    .join(""),
                }}
              />
            </Section>

            <Section title="Gợi ý">
              <ol className="list-decimal space-y-1 pl-5">
                {assignment.hints.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ol>
            </Section>
          </div>
        </aside>

        {/* RIGHT: editor + judge */}
        <main className="flex min-h-0 flex-col bg-[#F6F7FA]">
          <div className="flex-1 overflow-hidden p-4">
            <CodeEditorMock value={code} onChange={setCode} language="java" />
          </div>

          <div className="max-h-[40%] overflow-y-auto border-t border-border bg-card">
            <div className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">
                  Judge Console
                </h3>
                <span className="text-xs text-muted-foreground">
                  {results.filter((r) => r.status === "passed").length}/
                  {results.length} test case
                </span>
              </div>
              <div className="space-y-1.5">
                {results.map((tc) => (
                  <JudgeRow key={tc.id} tc={tc} />
                ))}
              </div>
            </div>
          </div>

          {/* Action bar */}
          <div className="shrink-0 border-t border-border bg-card px-4 py-3">
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="default"
                onClick={handleRun}
                disabled={running !== "idle"}
                className="min-w-28"
              >
                <Play className="size-4" />
                {running === "running" ? "Đang chạy..." : "Chạy thử"}
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={running !== "idle"}
                className="min-w-32"
                style={{ background: BRAND.primary }}
              >
                <Send className="size-4" />
                {running === "submitting" ? "Đang nộp..." : "Nộp bài"}
              </Button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
