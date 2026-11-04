"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";

import { DICTIONARY, type TranslationKey } from "./dictionary";
import {
  DEFAULT_LOCALE,
  getLocaleServerSnapshot,
  getLocaleSnapshot,
  isLocale,
  LOCALE_STORAGE_KEY,
  setStoredLocale,
  subscribeLocale,
  type Locale,
} from "./locale";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
  /** Tra cứu bản dịch theo key; hỗ trợ tham số `{name}`. */
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

/**
 * Provider ngôn ngữ.
 *
 * Dùng `useSyncExternalStore` để đọc locale:
 *  - Server render trả "vi" (getServerSnapshot) → HTML đầu tiên khớp client.
 *  - Client đọc localStorage (getSnapshot) → khôi phục ngôn ngữ đã chọn.
 *  - Đổi locale gọi `setStoredLocale` → store báo các subscriber re-render.
 */
export function LocaleProvider({ children }: { children: ReactNode }) {
  const locale = useSyncExternalStore(
    subscribeLocale,
    getLocaleSnapshot,
    getLocaleServerSnapshot,
  );

  const setLocale = useCallback((next: Locale) => {
    if (!isLocale(next)) return;
    setStoredLocale(next);
  }, []);

  const toggleLocale = useCallback(() => {
    setStoredLocale(locale === "vi" ? "en" : "vi");
  }, [locale]);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>) => {
      const entry = DICTIONARY[key];
      let text = entry ? entry[locale] : key;
      if (params) {
        for (const [name, value] of Object.entries(params)) {
          text = text.replaceAll(`{${name}}`, String(value));
        }
      }
      return text;
    },
    [locale],
  );

  const value = useMemo(
    () => ({ locale, setLocale, toggleLocale, t }),
    [locale, setLocale, toggleLocale, t],
  );

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

/** Hàm dịch fallback dùng chung — ổn định tham chiếu để không phá useMemo. */
const FALLBACK_TRANSLATE = (key: TranslationKey, params?: Record<string, string | number>) => {
  let text = DICTIONARY[key]?.[DEFAULT_LOCALE] ?? key;
  if (params) {
    for (const [name, value] of Object.entries(params)) {
      text = text.replaceAll(`{${name}}`, String(value));
    }
  }
  return text;
};

/**
 * Hook truy cập ngôn ngữ hiện tại + hàm dịch.
 *
 * Ngoài provider (ví dụ trong unit test), trả về locale mặc định và hàm dịch
 * dựa trên dictionary — để component vẫn render được thay vì crash.
 */
export function useLocale() {
  const context = useContext(LocaleContext);
  if (context) return context;

  return {
    locale: DEFAULT_LOCALE,
    setLocale: () => {},
    toggleLocale: () => {},
    t: FALLBACK_TRANSLATE,
  };
}

/** Hook rút gọn: chỉ cần hàm dịch. */
export function useTranslation() {
  return useLocale().t;
}

export { LOCALE_STORAGE_KEY };
