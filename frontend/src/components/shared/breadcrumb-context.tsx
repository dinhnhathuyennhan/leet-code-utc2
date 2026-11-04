"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";

import type { TranslationKey } from "@/lib/i18n";

// Cho page động (vd: /teacher/courses/[id]) đặt nhãn breadcrumb = mã lớp sau khi tải xong dữ liệu.

interface BreadcrumbContextValue {
  labels: {
    course: string | TranslationKey | null;
    session: string | TranslationKey | null;
    page: string | TranslationKey | null;
  };
  setLabel: (label: string | TranslationKey | null, kind: "course" | "session" | "page") => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue>({
  labels: { course: null, session: null, page: null },
  setLabel: () => {},
});

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [labels, setLabels] = useState({
    course: null as string | TranslationKey | null,
    session: null as string | TranslationKey | null,
    page: null as string | TranslationKey | null,
  });
  const setLabel = useCallback(
    (label: string | TranslationKey | null, kind: "course" | "session" | "page") =>
      setLabels((current) => ({ ...current, [kind]: label })),
    [],
  );
  const value = useMemo(() => ({ labels, setLabel }), [labels, setLabel]);
  return <BreadcrumbContext.Provider value={value}>{children}</BreadcrumbContext.Provider>;
}

/**
 * Page gọi: useBreadcrumbLabel("CS101")
 *
 * Dùng useLayoutEffect (không useEffect) để set label CHẬM hơn render nhưng
 * SỚM hơn browser paint → Topbar đã re-render với label mới trước khi user nhìn thấy.
 * Tránh flash "…" / "—" ở frame đầu.
 *
 * useLayoutEffect chạy sync sau khi React commit DOM, trước khi browser paint.
 * Vì Topbar là anh em của page trong cùng provider, setState trong layout effect của page
 * sẽ khiến Topbar re-render trước paint → user thấy breadcrumb đúng từ frame đầu.
 */
export function useBreadcrumbLabel(label: string | TranslationKey | null | undefined) {
  const pathname = usePathname();
  const { setLabel } = useContext(BreadcrumbContext);
  const kind = pathname.includes("/sessions/") ? "session" : "course";
  useEffect(() => {
    setLabel(label ?? null, kind);
    return () => setLabel(null, kind);
  }, [kind, label, setLabel]);
}

export function useBreadcrumbLabels(
  course: string | TranslationKey | null | undefined,
  session: string | TranslationKey | null | undefined,
  page?: string | TranslationKey | null,
) {
  const { setLabel } = useContext(BreadcrumbContext);
  useEffect(() => {
    setLabel(course ?? null, "course");
    setLabel(session ?? null, "session");
    setLabel(page ?? null, "page");
    return () => {
      setLabel(null, "course");
      setLabel(null, "session");
      setLabel(null, "page");
    };
  }, [course, session, page, setLabel]);
}

export function useBreadcrumbValue(): {
  course: string | TranslationKey | null;
  session: string | TranslationKey | null;
  page: string | TranslationKey | null;
} {
  return useContext(BreadcrumbContext).labels;
}
