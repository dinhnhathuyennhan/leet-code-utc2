const pad = (n: number) => String(n).padStart(2, "0");

/** "2024-09-18T23:59:00" → "18/09 · 23:59" */
export function formatDeadline(iso: string): string {
  const d = new Date(iso);
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} · ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** → "30/12/2024" */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
}

/** → "14:30 hôm nay" hoặc "14:30 18/09" */
export function formatUpdatedAt(iso: string): string {
  const d = new Date(iso);
  const time = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  return d.toDateString() === new Date().toDateString()
    ? `${time} hôm nay`
    : `${time} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}`;
}

/** → "HK1 (2024 - 2025) · Nhóm 02" */
export function formatTerm(c: { semester: number; academic_year: string; group: number }): string {
  return `HK${c.semester} (${c.academic_year.replace("-", " - ")}) · Nhóm ${pad(c.group)}`;
}

/** Chữ cái đầu của tên gọi (từ cuối cùng): "Nguyễn Văn An" → "A" */
export function getInitial(fullName: string): string {
  return fullName.trim().split(/\s+/).pop()?.charAt(0).toUpperCase() ?? "?";
}
