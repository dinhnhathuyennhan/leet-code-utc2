/**
 * Hệ thống i18n tự chứa (không phụ thuộc thư viện ngoài).
 *
 * - `Locale` = "vi" | "en"
 * - Locale được lưu ở localStorage (key `utc2:locale`) và đồng bộ với
 *   `document.documentElement.lang` để hỗ trợ SEO + screen reader.
 * - Store dùng mẫu `useSyncExternalStore`:
 *   1. Server render luôn trả "vi" (không lệch với client → không hydration mismatch).
 *   2. Sau hydration, client đọc localStorage và re-render → chuyển ngôn ngữ
 *      ngay lập tức mà không cần reload trang.
 */

export type Locale = "vi" | "en";

export const LOCALES: readonly Locale[] = ["vi", "en"];
export const DEFAULT_LOCALE: Locale = "vi";
export const LOCALE_STORAGE_KEY = "utc2:locale";

/** Nhãn hiển thị trên toggle (luôn dùng mã ngôn ngữ, không dịch). */
export const LOCALE_LABELS: Record<Locale, string> = {
  vi: "VI",
  en: "EN",
};

export function isLocale(value: unknown): value is Locale {
  return value === "vi" || value === "en";
}

/** Đọc locale đã lưu (chỉ gọi được ở client). */
export function readStoredLocale(): Locale {
  if (typeof window === "undefined") return DEFAULT_LOCALE;
  try {
    const raw = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    return isLocale(raw) ? raw : DEFAULT_LOCALE;
  } catch {
    // localStorage bị chặn (private mode / iframe sandbox) → dùng mặc định.
    return DEFAULT_LOCALE;
  }
}

export function writeStoredLocale(locale: Locale): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    // Bỏ qua — ngôn ngữ vẫn đổi trong phiên hiện tại.
  }
}

/** Gắn `lang` vào <html> để trình đọc màn hình đọc đúng ngôn ngữ. */
export function applyDocumentLang(locale: Locale): void {
  if (typeof document === "undefined") return;
  document.documentElement.lang = locale;
}

/* ── Store dùng chung (module-level) ─────────────────────────────────────
 * Dùng store thay vì useState + effect để:
 *  - Không vi phạm rule `react-hooks/set-state-in-effect`.
 *  - Đọc localStorage an toàn qua getServerSnapshot (SSR trả "vi").
 *  - Nhiều component cùng nghe 1 nguồn sự thật.
 * ------------------------------------------------------------------------ */

type Listener = () => void;

const listeners = new Set<Listener>();
let currentLocale: Locale = DEFAULT_LOCALE;
let initialized = false;

/** Đọc localStorage đúng 1 lần trên client (lazy init). */
function ensureInitialized(): void {
  if (initialized) return;
  initialized = true;
  if (typeof window !== "undefined") {
    currentLocale = readStoredLocale();
  }
}

/** Snapshot cho client (sau hydration). */
export function getLocaleSnapshot(): Locale {
  ensureInitialized();
  return currentLocale;
}

/** Snapshot cho server render — luôn là mặc định để khớp HTML đầu tiên. */
export function getLocaleServerSnapshot(): Locale {
  return DEFAULT_LOCALE;
}

/** Đăng ký listener để re-render khi locale đổi. */
export function subscribeLocale(listener: Listener): () => void {
  ensureInitialized();
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Đổi locale toàn cục + persist + thông báo các subscriber. */
export function setStoredLocale(next: Locale): void {
  ensureInitialized();
  if (!isLocale(next) || next === currentLocale) return;
  currentLocale = next;
  writeStoredLocale(next);
  applyDocumentLang(next);
  listeners.forEach((listener) => listener());
}

/**
 * Reset store về trạng thái ban đầu — chỉ dùng cho unit test.
 *
 * Cần thiết vì `currentLocale` sống ở module scope: giữa các test cần
 * nạp lại localStorage từ đầu (mô phỏng "reload trang").
 */
export function resetLocaleStore(): void {
  initialized = false;
  currentLocale = DEFAULT_LOCALE;
  listeners.clear();
}
