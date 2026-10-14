import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/error";

/** Retry transient network and server failures only. */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= 1) return false;
  if (error instanceof ApiError) {
    return error.isNetworkError || error.status >= 500;
  }
  return false;
}

export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: shouldRetry,
        staleTime: 30_000,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/** Shared query-key namespace for account data. */
export const accountsQueryKey = ["accounts"] as const;
