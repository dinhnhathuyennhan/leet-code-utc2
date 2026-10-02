"use client";

import { createContext, useContext, type ComponentProps, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface ToggleContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const ToggleContext = createContext<ToggleContextValue | null>(null);

export function ToggleGroup({ value = "", onValueChange, className, children, ...props }: ComponentProps<"div"> & { type?: "single"; value?: string; onValueChange?: (value: string) => void; children?: ReactNode }) {
  return (
    <ToggleContext.Provider value={{ value, onValueChange: onValueChange ?? (() => undefined) }}>
      <div className={cn("inline-flex", className)} {...props}>{children}</div>
    </ToggleContext.Provider>
  );
}

export function ToggleGroupItem({ value, className, children, ...props }: ComponentProps<"button"> & { value: string }) {
  const context = useContext(ToggleContext);
  const active = context?.value === value;
  return <button type="button" aria-pressed={active} data-state={active ? "on" : "off"} className={cn(className)} onClick={() => context?.onValueChange(value)} {...props}>{children}</button>;
}
