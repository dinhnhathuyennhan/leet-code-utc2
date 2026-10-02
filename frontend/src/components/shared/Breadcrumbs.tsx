import Link from "next/link";
import { Home } from "lucide-react";

import type { Crumb } from "@/lib/helpers/breadcrumbs";

export function Breadcrumbs({ homeHref, crumbs }: { homeHref: string; crumbs: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-sm sm:text-base">
      <Link href={homeHref} aria-label="Trang chủ" className="text-slate-500 transition-colors hover:text-indigo-600">
        <Home className="size-5" />
      </Link>
      {crumbs.map((crumb) => (
        <span key={crumb.label + (crumb.href ?? "")} className="flex min-w-0 items-center gap-2">
          <span aria-hidden className="text-slate-400">/</span>
          {crumb.href ? (
            <Link href={crumb.href} className="truncate font-medium text-foreground hover:text-indigo-600">
              {crumb.label}
            </Link>
          ) : (
            <span aria-current="page" className="truncate font-semibold text-indigo-600">
              {crumb.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}
