"use client";

import { cloneElement, createContext, useContext, useState, type ComponentProps, type ReactElement, type ReactNode } from "react";
import { cn } from "@/lib/utils";

const MenuContext = createContext<{ open: boolean; setOpen: (open: boolean) => void } | null>(null);

export function DropdownMenu({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return <MenuContext.Provider value={{ open, setOpen }}><div className="relative">{children}</div></MenuContext.Provider>;
}

export function DropdownMenuTrigger({ asChild, children, ...props }: ComponentProps<"button"> & { asChild?: boolean }) {
  const context = useContext(MenuContext);
  if (asChild && typeof children === "object" && children !== null && "type" in children) {
    const child = children as ReactElement<ComponentProps<"button">>;
    return cloneElement(child, { ...props, onClick: () => context?.setOpen(!context.open) });
  }
  return <button type="button" {...props} onClick={() => context?.setOpen(!context.open)}>{children}</button>;
}

export function DropdownMenuContent({ className, children, ...props }: ComponentProps<"div"> & { align?: "start" | "end" }) {
  const context = useContext(MenuContext);
  if (!context?.open) return null;
  return <div role="menu" className={cn("absolute right-0 z-50 mt-2 min-w-40 rounded-lg border bg-card p-1 shadow-lg", className)} {...props}>{children}</div>;
}

export function DropdownMenuItem({ className, onSelect, asChild = false, children, ...props }: ComponentProps<"button"> & { asChild?: boolean; onSelect?: () => void }) {
  const context = useContext(MenuContext);
  const itemClassName = cn("flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-muted", className);
  const handleSelect = () => {
    onSelect?.();
    context?.setOpen(false);
  };

  if (asChild && typeof children === "object" && children !== null && "type" in children) {
    const child = children as ReactElement<{ className?: string; onClick?: () => void; role?: string }>;
    return cloneElement(child, {
      ...props,
      role: "menuitem",
      className: cn(itemClassName, child.props.className),
      onClick: handleSelect,
    });
  }

  return <button type="button" role="menuitem" className={itemClassName} onClick={handleSelect} {...props}>{children}</button>;
}

export function DropdownMenuSeparator({ className, ...props }: ComponentProps<"div">) {
  return <div role="separator" className={cn("my-1 h-px bg-border", className)} {...props} />;
}
