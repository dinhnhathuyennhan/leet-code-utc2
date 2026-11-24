// Chạy Vitest với thư mục làm việc có ký tự ổ đĩa viết hoa.
// Trên Windows, khi terminal mở thư mục bằng `e:\...` (VS Code hay làm vậy), Vitest nạp hai bản
// @vitest/runner theo `e:` và `E:` → mọi test hỏng với lỗi "Vitest failed to find the runner".
import { spawnSync } from "node:child_process";
import path from "node:path";

const cwd = process.cwd().replace(/^[a-z]:/, (drive) => drive.toUpperCase());
const bin = path.join(cwd, "node_modules", "vitest", "vitest.mjs");
const result = spawnSync(process.execPath, [bin, ...process.argv.slice(2)], { cwd, stdio: "inherit" });

if (result.error) throw result.error;
process.exit(result.status ?? 1);
