"use client";

import { Braces, Gauge, Layers, Terminal } from "lucide-react";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { ProblemGradingMode } from "@/lib/api/endpoints/problems";
import { cn } from "@/lib/utils";

export type ProblemLevelFilter = "" | "easy" | "medium" | "hard";
export type ProblemGradingModeFilter = "" | ProblemGradingMode;

/** base-ui Select không nhận value rỗng: dùng giá trị đại diện cho "Tất cả". */
const ALL = "__all__";

const TRIGGER =
  "h-9 min-w-[168px] gap-2 rounded-lg border-input bg-background px-3 text-sm font-medium shadow-xs hover:bg-accent/40 data-popup-open:border-indigo-300 data-popup-open:ring-3 data-popup-open:ring-indigo-100";
const CONTENT = "min-w-[200px] rounded-xl p-1.5 shadow-lg";
const ITEM = "rounded-lg py-2 pr-8 pl-2.5";

const LEVEL_OPTIONS: Array<{ value: Exclude<ProblemLevelFilter, "">; label: string; dot: string }> = [
  { value: "easy", label: "Dễ", dot: "bg-emerald-500" },
  { value: "medium", label: "Trung bình", dot: "bg-amber-500" },
  { value: "hard", label: "Khó", dot: "bg-red-500" },
];

const GRADING_OPTIONS: Array<{ value: ProblemGradingMode; label: string; hint: string; icon: typeof Braces }> = [
  { value: "harness", label: "Function-call", hint: "harness", icon: Braces },
  { value: "stdin_stdout", label: "stdin/stdout", hint: "đọc/ghi chuẩn", icon: Terminal },
];

function Dot({ className }: { className: string }) {
  return <span aria-hidden className={cn("size-2 shrink-0 rounded-full", className)} />;
}

export function ProblemLevelSelect({
  value,
  onChange,
  className,
  allLabel = "Tất cả mức độ",
}: {
  value: ProblemLevelFilter;
  onChange: (value: ProblemLevelFilter) => void;
  className?: string;
  allLabel?: string;
}) {
  const current = LEVEL_OPTIONS.find((option) => option.value === value);
  return (
    <Select value={value || ALL} onValueChange={(next) => onChange(next === ALL || !next ? "" : (next as ProblemLevelFilter))}>
      <SelectTrigger aria-label="Lọc mức độ" className={cn(TRIGGER, className)}>
        <SelectValue>
          {current ? <><Dot className={current.dot} />{current.label}</> : <><Gauge className="size-4 text-muted-foreground" />{allLabel}</>}
        </SelectValue>
      </SelectTrigger>
      <SelectContent className={CONTENT}>
        <SelectItem value={ALL} className={ITEM}><Gauge className="size-4 text-muted-foreground" />{allLabel}</SelectItem>
        {LEVEL_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value} className={ITEM}>
            <Dot className={option.dot} />{option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function ProblemGradingModeSelect({
  value,
  onChange,
  className,
}: {
  value: ProblemGradingModeFilter;
  onChange: (value: ProblemGradingModeFilter) => void;
  className?: string;
}) {
  const current = GRADING_OPTIONS.find((option) => option.value === value);
  const CurrentIcon = current?.icon ?? Layers;
  return (
    <Select value={value || ALL} onValueChange={(next) => onChange(next === ALL || !next ? "" : (next as ProblemGradingMode))}>
      <SelectTrigger aria-label="Lọc cách chấm" className={cn(TRIGGER, className)}>
        <SelectValue>
          <CurrentIcon className={cn("size-4", current ? "text-indigo-600" : "text-muted-foreground")} />
          {current?.label ?? "Tất cả cách chấm"}
        </SelectValue>
      </SelectTrigger>
      <SelectContent className={CONTENT}>
        <SelectItem value={ALL} className={ITEM}><Layers className="size-4 text-muted-foreground" />Tất cả cách chấm</SelectItem>
        {GRADING_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value} className={ITEM}>
            <option.icon className="size-4 text-indigo-600" />
            {option.label}
            <span className="text-xs text-muted-foreground">{option.hint}</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
