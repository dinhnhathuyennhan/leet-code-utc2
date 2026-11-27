/**
 * Chặn JSDoc "mồ côi": hai khối `/** ... *\/` đứng liền nhau thì khối trên không còn gắn
 * với symbol nào — thường do chèn helper (kèm doc của nó) vào giữa doc có sẵn và hàm của
 * doc đó, khiến editor hiện doc ở sai hàm (vd: `stateAfterFailedRefresh` từng nằm giữa
 * JSDoc của `buildUserFromAccessToken` và hàm đó trong context/auth-context.tsx).
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { expect, it } from "vitest";

const SRC = path.resolve(__dirname, "..");

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) return sourceFiles(full);
    return /\.(ts|tsx)$/.test(name) ? [full] : [];
  });
}

/**
 * Vị trí (file:dòng) của mọi khối JSDoc bị khối JSDoc khác che ngay bên dưới.
 * Chỉ bắt hai khối liền sát (không có dòng trống giữa): có dòng trống thì thường là chủ ý —
 * tiêu đề section `/* ─── *\/` hay doc đầu file đứng riêng.
 */
function findOrphanJsDocs(files: string[]): string[] {
  const stacked = /\*\/[ \t]*\r?\n[ \t]*\/\*\*/g;
  return files.flatMap((file) => {
    const text = readFileSync(file, "utf8");
    return Array.from(text.matchAll(stacked), (match) => {
      const line = text.slice(0, match.index).split("\n").length;
      return `${path.relative(SRC, file)}:${line}`;
    });
  });
}

it("has no JSDoc block stacked directly on top of another one", () => {
  expect(findOrphanJsDocs(sourceFiles(SRC))).toEqual([]);
});
