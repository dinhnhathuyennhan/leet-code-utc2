"use client";

import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";

import { useBreadcrumbValue } from "@/components/shared/breadcrumb-context";
import { TopbarActions } from "@/components/shared/topbar-actions";
import { Button } from "@/components/ui/button";
import { buildBreadcrumbs } from "@/lib/helpers/breadcrumbs";
import { Breadcrumbs } from "@/components/shared/Breadcrumbs";

interface TopbarProps {
  homeHref: string;
  onMenuClick: () => void;
  onLogout: () => void;
}

export function Topbar({ homeHref, onMenuClick, onLogout }: TopbarProps) {
  const pathname = usePathname();
  const dynamicLabel = useBreadcrumbValue();
  const crumbs = buildBreadcrumbs(pathname, dynamicLabel);

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b bg-card/85 px-4 backdrop-blur sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-2">
        <Button variant="ghost" size="icon" onClick={onMenuClick} aria-label="Mở menu" className="lg:hidden">
          <Menu className="size-5" />
        </Button>
        <Breadcrumbs homeHref={homeHref} crumbs={crumbs} />
      </div>
      <TopbarActions onLogout={onLogout} />
    </header>
  );
}
