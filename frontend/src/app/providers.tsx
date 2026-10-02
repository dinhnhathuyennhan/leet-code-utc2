"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ThemeProvider } from "next-themes";
import { Suspense, useState, type ReactNode } from "react";

import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/auth-context";
import { makeQueryClient } from "@/lib/query-client";
import { RouteGuard } from "./route-guard";
import { Loader2 } from "lucide-react";

export function Providers({ children }: { children: ReactNode }) {
  // useState (not module scope) so each request/browser session gets its
  // own QueryClient — the documented Next.js App Router pattern.
  const [queryClient] = useState(() => makeQueryClient());

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Suspense
          fallback={
              <div className="flex h-[100dvh] w-full items-center justify-center bg-slate-900" aria-busy="true">
                <Loader2 className="size-8 animate-spin text-white" />
              </div>
            }>
            <RouteGuard>
              {children}
              <Toaster />
            </RouteGuard>
          </Suspense> 
        </AuthProvider>
        {process.env.NODE_ENV !== "production" && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </ThemeProvider>
  );
}
