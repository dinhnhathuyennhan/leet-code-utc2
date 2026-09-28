import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Badge({ className, variant: _variant, ...props }: ComponentProps<"span"> & { variant?: string }) {
  void _variant;
  return <span className={cn("inline-flex items-center", className)} {...props} />;
}
