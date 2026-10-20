export function downloadCsv(filename: string, rows: Array<Array<string | number | null | undefined>>): void {
  downloadExcel(filename.replace(/\.csv$/i, ".xls"), rows);
}

export function downloadExcel(
  filename: string,
  headersOrRows: Array<string | number> | Array<Array<string | number | null | undefined>>,
  optionalRows?: Array<Array<string | number | null | undefined>>,
): void {
  const rows = optionalRows ?? (headersOrRows as Array<Array<string | number | null | undefined>>).slice(1);
  const headers = optionalRows ? headersOrRows as Array<string | number> : (headersOrRows as Array<Array<string | number | null | undefined>>)[0] ?? [];
  const escapeHtml = (value: string | number | null | undefined) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  const header = headers.map((value) => `<th style="background:#34227a;color:#fff;border:1px solid #d8d3ed;padding:8px;font-weight:700">${escapeHtml(value)}</th>`).join("");
  const body = rows.map((row) => `<tr>${row.map((value) => `<td style="border:1px solid #d8d3ed;padding:8px;color:#1e1b4b">${escapeHtml(value)}</td>`).join("")}</tr>`).join("");
  const html = `<html><head><meta charset="UTF-8"></head><body><table style="border-collapse:collapse;font-family:Arial,'Segoe UI',sans-serif;font-size:12px"><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></body></html>`;
  const blob = new Blob(["\ufeff", html], { type: "application/vnd.ms-excel;charset=utf-8" });
  const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename.endsWith(".xls") ? filename : `${filename}.xls`; anchor.click(); URL.revokeObjectURL(url);
}
