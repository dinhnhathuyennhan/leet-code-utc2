export type DraftTestcase = { id: number; input: string; expected_output: string; is_sample: boolean; inputValue?: unknown[]; outputValue?: unknown };

export type TestcaseValidationErrors = Record<number, { input?: string; output?: string }>;

export function jsonText(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value;
  try { return JSON.stringify(value, null, 2) ?? fallback; } catch { return fallback; }
}

/** Chuỗi hiển thị cho giáo viên; không render ngoặc mảng trên giao diện. */
export function displayInput(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map((item) => displayInput(item)).join(", ");
  return String(value ?? "");
}

export function displayOutput(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map((item) => displayOutput(item)).join(", ");
  return String(value ?? "");
}

function parseToken(value: string): unknown {
  try { return JSON.parse(value); } catch { return value; }
}

/** Cho phép nhập thân thiện: `2, 7, 11, 15`, `2\n7`, `2` hoặc JSON array. */
export function parseInputText(raw: string): unknown[] {
  const value = raw.trim();
  if (!value) throw new Error("Input testcase không được để trống.");
  try {
    const parsed = JSON.parse(value) as unknown;
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch {
    return value.includes(",") || value.includes("\n")
      ? value.split(/,|\r?\n/).map((part) => part.trim()).filter(Boolean).map(parseToken)
      : [value];
  }
}

export function parseOutputText(raw: string): unknown {
  const value = raw.trim();
  if (!value) throw new Error("Output testcase không được để trống.");
  return parseToken(value);
}

export function parseDraftTestcases(items: DraftTestcase[]) {
  const errors: TestcaseValidationErrors = {};
  const parsed: Array<{ input: unknown[]; expected_output: unknown; is_sample: boolean }> = [];
  items.forEach((item, index) => {
    const fieldErrors: { input?: string; output?: string } = {};
    let input: unknown;
    let output: unknown;
    try { input = parseInputText(item.input); } catch (error) { fieldErrors.input = error instanceof Error ? error.message : "Input testcase không hợp lệ."; }
    try { output = parseOutputText(item.expected_output); } catch (error) { fieldErrors.output = error instanceof Error ? error.message : "Output testcase không hợp lệ."; }
    if (Object.keys(fieldErrors).length) errors[index] = fieldErrors;
    else parsed.push({ input: (item.inputValue ?? input) as unknown[], expected_output: item.outputValue ?? output, is_sample: item.is_sample });
  });
  if (!items.length) errors[0] = { input: "Bài tập phải có ít nhất một testcase." };
  return { parsed, errors };
}

function asImportedItems(payload: unknown): unknown[] {
  if (Array.isArray(payload)) return payload;
  if (payload && typeof payload === "object" && Array.isArray((payload as { testcases?: unknown }).testcases)) return (payload as { testcases: unknown[] }).testcases;
  throw new Error("File phải chứa một mảng testcase hoặc object có thuộc tính testcases.");
}

export function normalizeImportedTestcases(payload: unknown): { items: DraftTestcase[]; errors: string[] } {
  const errors: string[] = [];
  let values: unknown[];
  try { values = asImportedItems(payload); } catch (error) { return { items: [], errors: [error instanceof Error ? error.message : "Payload testcase không hợp lệ."] }; }
  if (!values.length) return { items: [], errors: ["File phải chứa ít nhất một testcase."] };
  const items = values.map((raw, index) => {
    const value = raw as { input?: unknown; expected_output?: unknown; is_sample?: unknown };
    if (!raw || typeof raw !== "object") { errors.push(`Dòng ${index + 1}: testcase phải là object.`); return { id: -Date.now() - index, input: "", expected_output: "", is_sample: false }; }
    if (value.input === undefined) errors.push(`Dòng ${index + 1}, field input: không được thiếu.`);
    if (value.expected_output === undefined) errors.push(`Dòng ${index + 1}, field expected_output: không được thiếu.`);
    if (value.is_sample !== undefined && typeof value.is_sample !== "boolean") errors.push(`Dòng ${index + 1}, field is_sample: phải là boolean.`);
    // Giữ nguyên chuỗi legacy (`1 2`, `hello`, ...) trên giao diện; chỉ chuẩn hóa
    // thành mảng ở bước tạo request gửi tới API hiện tại.
    const inputText = displayInput(value.input);
    return { id: -Date.now() - index, input: inputText, expected_output: displayOutput(value.expected_output), is_sample: value.is_sample === true, inputValue: Array.isArray(value.input) ? value.input : undefined, outputValue: value.expected_output };
  });
  return { items, errors };
}

async function unzipJson(file: File): Promise<string> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  for (let offset = 0; offset + 30 <= bytes.length;) {
    if (view.getUint32(offset, true) !== 0x04034b50) { offset += 1; continue; }
    const method = view.getUint16(offset + 8, true);
    const compressedSize = view.getUint32(offset + 18, true);
    const nameSize = view.getUint16(offset + 26, true);
    const extraSize = view.getUint16(offset + 28, true);
    const name = new TextDecoder().decode(bytes.slice(offset + 30, offset + 30 + nameSize));
    const start = offset + 30 + nameSize + extraSize;
    if (compressedSize > 20 * 1024 * 1024) throw new Error("File ZIP quá lớn.");
    if (name.toLowerCase().endsWith(".json")) {
      const data = bytes.slice(start, start + compressedSize);
      let output: ArrayBuffer;
      if (method === 0) output = data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength);
      else if (method === 8) output = await new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream("deflate-raw"))).arrayBuffer();
      else throw new Error("ZIP dùng kiểu nén không được hỗ trợ.");
      if (output.byteLength > 20 * 1024 * 1024) throw new Error("Payload JSON trong ZIP quá lớn.");
      return new TextDecoder().decode(output);
    }
    offset = start + compressedSize;
  }
  throw new Error("ZIP không chứa file JSON testcase.");
}

export async function readTestcaseFile(file: File): Promise<{ items: DraftTestcase[]; errors: string[]; raw: unknown[] }> {
  const name = file.name.toLowerCase();
  if (!name.endsWith(".json") && !name.endsWith(".zip")) return { items: [], errors: ["Đuôi file không hợp lệ. Chỉ chấp nhận file .json hoặc .zip."], raw: [] };
  try {
    const text = name.endsWith(".zip") ? await unzipJson(file) : await file.text();
    const payload = JSON.parse(text) as unknown;
    const normalized = normalizeImportedTestcases(payload);
    return { ...normalized, raw: normalized.items.map((item) => ({ input: item.inputValue ?? parseInputText(item.input), expected_output: item.outputValue ?? parseOutputText(item.expected_output), is_sample: item.is_sample })) };
  } catch (error) { return { items: [], errors: [error instanceof Error ? error.message : "Không đọc được file testcase."], raw: [] }; }
}
