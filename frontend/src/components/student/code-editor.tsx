"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, Copy, FileCode2, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  LANGUAGE_OPTIONS,
  findLanguageOption,
  starterCodeFor,
  type LanguageOption,
} from "@/lib/helpers/languages";
import { useLocale } from "@/lib/i18n";
import { cn } from "@/lib/utils";

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  /** Mã mẫu khởi tạo theo từng ngôn ngữ. */
  starterCodes?: Record<string, string>;
  /** Template fallback khi bài không có mã mẫu cho ngôn ngữ đang chọn. */
  fallbackCode?: string;
  language: string;
  onLanguageChange: (language: string) => void;
  /** Khóa tắt nút "Nộp bài" khi đang chấm. */
  disabled?: boolean;
}

/**
 * Ô soạn code cho sinh viên: chọn ngôn ngữ, soạn code, copy và khôi phục mẫu.
 *
 * Khi đổi ngôn ngữ, code hiện tại được giữ lại nếu người dùng đã sửa; nếu chưa
 * sửa gì thì nạp mã mẫu của ngôn ngữ mới cho tiện.
 */
export function CodeEditor({
  value,
  onChange,
  starterCodes,
  fallbackCode = "",
  language,
  onLanguageChange,
  disabled = false,
}: CodeEditorProps) {
  const [copied, setCopied] = useState(false);
  const [touched, setTouched] = useState(false);
  const { t } = useLocale();

  const options: LanguageOption[] = useMemo(() => LANGUAGE_OPTIONS, []);
  const current = findLanguageOption(language) ?? options[0];

  // Nạp mã mẫu của ngôn ngữ đang chọn khi người dùng chưa tự sửa code.
  useEffect(() => {
    if (touched) return;
    const starter = starterCodeFor(language, starterCodes, fallbackCode);
    onChange(starter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  async function copyCode() {
    try {
      await navigator.clipboard?.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard bị chặn (không có quyền) — bỏ qua, không chặn luồng chính.
    }
  }

  function resetCode() {
    setTouched(false);
    onChange(starterCodeFor(language, starterCodes, fallbackCode));
  }

  return (
    <section className="flex min-h-[560px] flex-col overflow-hidden rounded-2xl border bg-slate-950">
      {/* ── Thanh công cụ ─────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 px-3 py-2">
        <div className="flex items-center gap-1 overflow-x-auto">
          {options.map((option) => {
            const active = option.value === language;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onLanguageChange(option.value);
                }}
                disabled={disabled}
                aria-pressed={active}
                className={cn(
                  "inline-flex shrink-0 items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "bg-white/15 text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200",
                )}
              >
                <span className={cn("size-2 rounded-full", option.tone)} />
                {option.label}
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="xs"
            onClick={resetCode}
            disabled={disabled}
            className="text-slate-400 hover:bg-white/10 hover:text-slate-100"
          >
            <RotateCcw className="size-3.5" /> {t("editor.reset")}
          </Button>
          <Button
            variant="ghost"
            size="xs"
            onClick={() => void copyCode()}
            disabled={disabled}
            className="text-slate-400 hover:bg-white/10 hover:text-slate-100"
          >
            {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
            {copied ? t("action.copied") : t("action.copy")}
          </Button>
        </div>
      </div>

      {/* ── Tên file ─────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 border-b border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300">
        <FileCode2 className="size-3.5 text-sky-400" />
        <span className="font-mono">Main.{current.extension}</span>
      </div>

      {/* ── Ô soạn code ──────────────────────────────────────────────── */}
      <textarea
        value={value}
        onChange={(event) => {
          setTouched(true);
          onChange(event.target.value);
        }}
        disabled={disabled}
        spellCheck={false}
        aria-label={t("editor.sourceLabel")}
        className="min-h-0 flex-1 resize-none bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-100 outline-none disabled:opacity-60"
      />
    </section>
  );
}
