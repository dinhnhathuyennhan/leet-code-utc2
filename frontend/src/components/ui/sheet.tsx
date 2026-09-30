"use client";

import { createContext, useContext, type ComponentProps, type ReactNode } from "react";
import { cn } from "@/lib/utils";

const SheetContext = createContext(false);

export function Sheet({ open, children }: { open: boolean; onOpenChange: (open: boolean) => void; children: ReactNode }) {
  return <SheetContext.Provider value={open}>{children}</SheetContext.Provider>;
}

export function SheetContent({ className, children, side = "left", ...props }: ComponentProps<"aside"> & { side?: "left" | "right" }) {
  const open = useContext(SheetContext);
  if (!open) return null;
  return <aside className={cn("fixed inset-y-0 z-50 w-72 bg-card shadow-xl", side === "left" ? "left-0" : "right-0", className)} {...props}>{children}</aside>;
}

export function SheetTitle({ className, ...props }: ComponentProps<"h2">) { return <h2 className={cn(className)} {...props} />; }
export function SheetDescription({ className, ...props }: ComponentProps<"p">) { return <p className={cn(className)} {...props} />; }
