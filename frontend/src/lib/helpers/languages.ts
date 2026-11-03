// ─── Ngôn ngữ lập trình hỗ trợ cho sinh viên nộp bài ──────────────────────────

export interface LanguageOption {
  /** Khóa gửi lên backend (đồng thời là key trong `starter_codes`). */
  value: string;
  label: string;
  /** Đuôi file hiển thị trên tab editor. */
  extension: string;
  /** Màu nhấn của tab / badge. */
  tone: string;
}

/**
 * Danh sách ngôn ngữ mà backend + Judge0 hỗ trợ.
 * Phải khớp với `_DEFAULT_LANGUAGES` trong `backend/app/core/config.py`.
 */
export const LANGUAGE_OPTIONS: LanguageOption[] = [
  { value: "python", label: "Python 3.8", extension: "py", tone: "bg-sky-500" },
  { value: "cpp", label: "C++ (GCC 9.2)", extension: "cpp", tone: "bg-blue-600" },
  { value: "java", label: "Java 13", extension: "java", tone: "bg-orange-500" },
  { value: "c", label: "C (GCC 9.2)", extension: "c", tone: "bg-slate-600" },
  { value: "javascript", label: "JavaScript (Node 12)", extension: "js", tone: "bg-amber-500" },
];

/** Tìm option theo khóa ngôn ngữ. */
export function findLanguageOption(value: string): LanguageOption | undefined {
  return LANGUAGE_OPTIONS.find((option) => option.value === value);
}

/**
 * Mã mẫu tối thiểu cho từng ngôn ngữ.
 *
 * Dữ liệu seed hiện chỉ có template Python. Nếu sinh viên chọn C++/Java mà
 * không đổi mã, editor sẽ hiển thị code Python -> nộp lên chắc chắn báo lỗi
 * biên dịch và gây nhầm lẫn. Vì vậy mỗi ngôn ngữ có một skeleton riêng, chỉ
 * dùng khi bài không có sẵn `starter_codes` cho ngôn ngữ đó.
 */
export const DEFAULT_SKELETONS: Record<string, string> = {
  python: "def solve():\n    # TODO: viết lời giải\n    pass\n\n\nsolve()\n",
  cpp:
    "#include <iostream>\nusing namespace std;\n\nint main() {\n    // TODO: viet loi giai\n    return 0;\n}\n",
  c: "#include <stdio.h>\n\nint main() {\n    // TODO: viet loi giai\n    return 0;\n}\n",
  java:
    "import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        // TODO: viet loi giai\n    }\n}\n",
  javascript:
    "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\n\n// TODO: viet loi giai\n",
};

/** Mã mẫu tối thiểu theo ngôn ngữ (dùng khi bài không có starter code riêng). */
export function defaultStarterCode(language: string): string {
  return DEFAULT_SKELETONS[language] ?? "";
}

/**
 * Chọn mã mẫu khởi tạo cho một ngôn ngữ.
 *
 * Thứ tự ưu tiên:
 * 1. `starterCodes[language]` — template đúng ngôn ngữ do giáo viên cấu hình.
 * 2. `fallback` — template chung của bài (thường là Python legacy).
 * 3. Skeleton tối thiểu theo ngôn ngữ — tránh hiển thị code Python trong
 *    tab C++/Java.
 *
 * Lưu ý: `fallback` chỉ dùng khi ngôn ngữ đang chọn LÀ python, nếu không thì
 * sẽ hiển thị sai ngôn ngữ. Với các ngôn ngữ khác, ưu tiên skeleton riêng.
 */
export function starterCodeFor(
  language: string,
  starterCodes: Record<string, string> | undefined,
  fallback: string,
): string {
  const specific = starterCodes?.[language];
  if (specific) return specific;

  // Template chung của bài chỉ hợp lệ khi bài đó viết bằng python.
  if (language === "python") return fallback || defaultStarterCode("python");

  return defaultStarterCode(language);
}
