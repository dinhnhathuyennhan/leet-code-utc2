"use client";

import { createContext, useContext, useLayoutEffect, useMemo, useState, type ReactNode } from "react";

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
export function useBreadcrumbLabel(label: string | null | undefined) {
  const { setLabel } = useContext(BreadcrumbContext);
  // useLayoutEffect chạy trên client. Trên server không có window/layout, nên guard.
  useLayoutEffect(() => {
    setLabel(label ?? null);
  }, [label, setLabel]);
}

export function useBreadcrumbValue(): string | null {
  return useContext(BreadcrumbContext).label;
}
