"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";

// Cho page động (vd: /teacher/courses/[id]) đặt nhãn breadcrumb = mã lớp sau khi tải xong dữ liệu.

interface BreadcrumbContextValue {
  labels: { course: string | null; session: string | null; page: string | null };
  setLabel: (label: string | null, kind: "course" | "session" | "page") => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue>({ labels: { course: null, session: null, page: null }, setLabel: () => {} });

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [labels, setLabels] = useState({ course: null as string | null, session: null as string | null, page: null as string | null });
  const setLabel = useCallback((label: string | null, kind: "course" | "session" | "page") => setLabels((current) => ({ ...current, [kind]: label })), []);
  const value = useMemo(() => ({ labels, setLabel }), [labels, setLabel]);
  return <BreadcrumbContext.Provider value={value}>{children}</BreadcrumbContext.Provider>;
}

/** Page gọi: useBreadcrumbLabel(course?.code) */
export function useBreadcrumbLabel(label: string | null | undefined) {
  const pathname = usePathname();
  const { setLabel } = useContext(BreadcrumbContext);
  const kind = pathname.includes("/sessions/") ? "session" : "course";
  useEffect(() => {
    setLabel(label ?? null, kind);
    return () => setLabel(null, kind);
  }, [kind, label, setLabel]);
}

export function useBreadcrumbLabels(course: string | null | undefined, session: string | null | undefined, page?: string | null) {
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

export function useBreadcrumbValue(): { course: string | null; session: string | null; page: string | null } {
  return useContext(BreadcrumbContext).labels;
}
