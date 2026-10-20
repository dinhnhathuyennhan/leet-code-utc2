// src/lib/helpers/datetime.ts
// Tất cả datetime từ API đều có offset +07:00. Dùng Intl.DateTimeFormat với
// timeZone: "Asia/Ho_Chi_Minh" để đảm bảo hiển thị đúng kể cả khi trình duyệt
// không ở múi giờ Việt Nam (dev dùng UTC, người dùng ở nước ngoài).

const VN_TZ = "Asia/Ho_Chi_Minh";

const vnFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: VN_TZ,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23", // 0 giờ hiển thị 00, không phải 24
});

function vnParts(value: string | Date): Record<string, string> {
  // Date-only fields (Lesson/Course calendar dates) are dates in the VN
  // calendar, not instants. Do not let Date parse them as UTC midnight.
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [year, month, day] = value.split("-");
    return { year, month, day, hour: "00", minute: "00" };
  }
  const parts = vnFormatter.formatToParts(new Date(value));
  return Object.fromEntries(parts.map((p) => [p.type, p.value]));
}

/** "2026-09-13T23:59:59.999999+07:00" → "13/09 · 23:59" trên mọi trình duyệt */
export function formatDeadline(iso: string): string {
  if (!iso) return "";
  try {
    const p = vnParts(iso);
    return `${p.day}/${p.month} · ${p.hour}:${p.minute}`;
  } catch {
    return iso;
  }
}

/** → "07/09/2026" */
export function formatDate(iso: string): string {
  if (!iso) return "";
  try {
    const p = vnParts(iso);
    return `${p.day}/${p.month}/${p.year}`;
  } catch {
    return iso;
  }
}

/** → "14:30 hôm nay" hoặc "14:30 18/09" */
export function formatUpdatedAt(iso: string): string {
  if (!iso) return "";
  try {
    const p = vnParts(iso);
    const todayInput = toDateInput(new Date());
    const isoInput = toDateInput(iso);
    const time = `${p.hour}:${p.minute}`;
    return isoInput === todayInput ? `${time} hôm nay` : `${time} ${p.day}/${p.month}`;
  } catch {
    return iso;
  }
}

/** Giá trị cho `<input type="date">`: "2026-09-07" theo lịch VN */
export function toDateInput(value: string | Date): string {
  try {
    const p = vnParts(value);
    return `${p.year}-${p.month}-${p.day}`;
  } catch {
    return typeof value === "string" ? value.slice(0, 10) : "";
  }
}

/** "2026-09-07" → "2026-09-07T00:00:00+07:00" để gửi lên API */
export function fromDateInput(value: string, time = "00:00:00"): string {
  return `${value}T${time}+07:00`;
}

/** [00:00 thứ Hai, 00:00 thứ Hai tuần sau) theo giờ VN */
export function vnWeekRange(now = new Date()): [Date, Date] {
  const today = toDateInput(now);
  const dayOfWeek = new Date(`${today}T12:00:00+07:00`).getUTCDay();
  const start = new Date(`${today}T00:00:00+07:00`);
  start.setUTCDate(start.getUTCDate() - ((dayOfWeek + 6) % 7));
  const end = new Date(start);
  end.setUTCDate(end.getUTCDate() + 7);
  return [start, end];
}
