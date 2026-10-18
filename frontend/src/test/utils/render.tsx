import { ReactElement, ReactNode } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthContext, AuthProvider } from "@/context/auth-context";
import type { UserResponse } from "@/lib/api/types";

const TEST_USER: UserResponse = {
  user_id: "SV001",
  role_id: 3,
  full_name: "Sinh viên Test",
  email: "sv001@test.local",
  must_change_password: false,
};

/**
 * Render component được bọc trong tất cả providers cần thiết.
 *
 * Theo mặc định sẽ mock auth state = "authenticated" với TEST_USER để test
 * component phụ thuộc auth (vd: dashboard lấy studentId từ auth.user) chạy
 * được. Truyền `auth: "unauthenticated"` để test nhánh khác.
 *
 * Chú ý: dùng AuthProvider thật nhưng bỏ qua bootstrap (refreshRequest) — xem
 * notes trong `vi.mock` ở dưới (test file nên mock axios nếu cần auth state).
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions & {
    queryClient?: QueryClient;
    auth?: "authenticated" | "unauthenticated";
  },
) {
  const queryClient =
    options?.queryClient ??
    new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: 0 },
        mutations: { retry: false },
      },
    });

  const authStatus = options?.auth ?? "authenticated";

  // Tránh gọi `refreshRequest()` thật (sẽ throw trong test vì không có
  // axios instance / refresh cookie): cung cấp AuthContext trực tiếp.
  function MockedAuthProvider({ children }: { children: ReactNode }) {
    return (
      <AuthContext.Provider
        value={
          {
            status: authStatus,
            user: authStatus === "authenticated" ? TEST_USER : undefined,
            login: async () => TEST_USER,
            changePassword: async () => TEST_USER,
            logout: async () => {},
          } as never
        }
      >
        {children}
      </AuthContext.Provider>
    );
  }

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MockedAuthProvider>{children}</MockedAuthProvider>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

// Silence unused import warning for AuthProvider (kept for API compatibility).
void AuthProvider;
