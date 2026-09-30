"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

// Cho page động (vd: /teacher/courses/[id]) đặt nhãn breadcrumb = mã lớp sau khi tải xong dữ liệu.

interface BreadcrumbContextValue {
  label: string | null;
  setLabel: (label: string | null) => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue>({ label: null, setLabel: () => {} });

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [label, setLabel] = useState<string | null>(null);
  const value = useMemo(() => ({ label, setLabel }), [label]);
  return <BreadcrumbContext.Provider value={value}>{children}</BreadcrumbContext.Provider>;
}

/** Page gọi: useBreadcrumbLabel(course?.code) */
export function useBreadcrumbLabel(label: string | null | undefined) {
  const { setLabel } = useContext(BreadcrumbContext);
  useEffect(() => {
    setLabel(label ?? null);
    return () => setLabel(null);
  }, [label, setLabel]);
}

export function useBreadcrumbValue(): string | null {
  return useContext(BreadcrumbContext).label;
}
