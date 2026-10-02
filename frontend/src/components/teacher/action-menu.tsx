"use client";

import { EllipsisVertical } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface ActionMenuItem {
  label: string;
  destructive?: boolean;
  onSelect?: () => void;
}

/** Nút ⋮ mở menu thao tác — dùng chung cho buổi học và bài tập. */
export function ActionMenu({ label, items, className }: { label: string; items: ActionMenuItem[]; className?: string }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label={label} className={className ?? "size-9 bg-indigo-50 text-slate-700 hover:bg-indigo-100 dark:bg-slate-800"}>
          <EllipsisVertical className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        {items.map((item, index) => (
          <div key={item.label}>
            {item.destructive && index > 0 && <DropdownMenuSeparator />}
            <DropdownMenuItem onSelect={item.onSelect} className={item.destructive ? "text-red-600 focus:text-red-600" : undefined}>
              {item.label}
            </DropdownMenuItem>
          </div>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
