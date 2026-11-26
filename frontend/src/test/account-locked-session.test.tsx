/**
 * Tài khoản bị khoá (403 `ACCOUNT_LOCKED`, docs/api-design-auth.md):
 *  - API bất kỳ / refresh trả ACCOUNT_LOCKED → xoá phiên, AuthProvider về "unauthenticated"
 *    với reason "account-locked", trang đăng nhập báo "Tài khoản đã bị khoá".
 *  - Đăng nhập đúng mật khẩu vào tài khoản bị khoá → báo khoá, không đánh dấu sai mật khẩu.
 *  - Lỗi phiên thường (refresh 401) vẫn là "expired", không báo khoá.
 */
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";

import { server } from "@/test/mocks/server";
import axiosInstance, { setSessionExpiredHandler } from "@/lib/axios";
import { getAccessToken, setAccessToken } from "@/lib/auth/token-store";
import { login } from "@/lib/api/endpoints/auth";
import { listUsers } from "@/lib/api/endpoints/admin";
import { AuthProvider, useAuth } from "@/context/auth-context";
import { LoginForm } from "@/components/shared/login-form";

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() } }));

const API = "http://localhost:8000";
const LOCKED_BODY = { error_code: "ACCOUNT_LOCKED", message: "Tài khoản đã bị khoá" };
const LOCKED_NOTICE = /Tài khoản đã bị khoá\. Vui lòng liên hệ/;

afterEach(() => {
  setSessionExpiredHandler(null);
  setAccessToken(null);
});

describe("axios interceptor", () => {
  it("ends the session as 'account-locked' when any API answers 403 ACCOUNT_LOCKED, without refreshing", async () => {
    const refresh = vi.fn();
    server.use(
      http.get(`${API}/users/me`, () => HttpResponse.json(LOCKED_BODY, { status: 403 })),
      http.post(`${API}/auth/refresh-access-token`, () => {
        refresh();
        return HttpResponse.json({ access_token: "x" });
      }),
    );
    const handler = vi.fn();
    setSessionExpiredHandler(handler);
    setAccessToken("token-before-lock");

    await expect(axiosInstance.get("/users/me")).rejects.toMatchObject({ response: { status: 403 } });
    expect(handler).toHaveBeenCalledWith("account-locked");
    expect(getAccessToken()).toBeNull();
    expect(refresh).not.toHaveBeenCalled();
  });

  it("ends the session as 'account-locked' when the refresh after a 401 answers ACCOUNT_LOCKED", async () => {
    server.use(
      http.get(`${API}/users/me`, () => HttpResponse.json({ error_code: "UNAUTHORIZED", message: "x" }, { status: 401 })),
      http.post(`${API}/auth/refresh-access-token`, () => HttpResponse.json(LOCKED_BODY, { status: 403 })),
    );
    const handler = vi.fn();
    setSessionExpiredHandler(handler);
    setAccessToken("old");

    await expect(axiosInstance.get("/users/me")).rejects.toBeTruthy();
    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler).toHaveBeenCalledWith("account-locked");
  });

  it("keeps a normal refresh failure as 'expired'", async () => {
    server.use(
      http.get(`${API}/users/me`, () => HttpResponse.json({ error_code: "UNAUTHORIZED", message: "x" }, { status: 401 })),
      http.post(`${API}/auth/refresh-access-token`, () =>
        HttpResponse.json({ error_code: "SESSION_EXPIRED", message: "Phiên đăng nhập đã hết hạn" }, { status: 401 }),
      ),
    );
    const handler = vi.fn();
    setSessionExpiredHandler(handler);
    setAccessToken("old");

    await expect(axiosInstance.get("/users/me")).rejects.toBeTruthy();
    expect(handler).toHaveBeenCalledWith("expired");
  });

  it("does not end any session for a locked login, but exposes the error code", async () => {
    server.use(http.post(`${API}/auth/login`, () => HttpResponse.json(LOCKED_BODY, { status: 403 })));
    const handler = vi.fn();
    setSessionExpiredHandler(handler);

    await expect(login({ email: "6851071001@st.utc2.edu.vn", password: "6851071001" })).rejects.toMatchObject({
      name: "ApiError",
      status: 403,
      code: "ACCOUNT_LOCKED",
      detail: "Tài khoản đã bị khoá",
    });
    expect(handler).not.toHaveBeenCalled();
  });

  it("keeps NOT_ALLOWED_TO_MANAGE_ACCOUNT as a normal error (no logout)", async () => {
    server.use(
      http.get(`${API}/users`, () =>
        HttpResponse.json({ error_code: "NOT_ALLOWED_TO_MANAGE_ACCOUNT", message: "Bạn không có quyền quản lý tài khoản này" }, { status: 403 }),
      ),
    );
    const handler = vi.fn();
    setSessionExpiredHandler(handler);
    setAccessToken("valid");

    await expect(listUsers()).rejects.toMatchObject({ code: "NOT_ALLOWED_TO_MANAGE_ACCOUNT", status: 403 });
    expect(handler).not.toHaveBeenCalled();
    expect(getAccessToken()).toBe("valid");
  });
});

function AuthProbe() {
  const auth = useAuth();
  return (
    <p data-testid="auth">
      {auth.status}
      {auth.status === "unauthenticated" && auth.reason ? `:${auth.reason}` : ""}
    </p>
  );
}

function renderWithAuth(ui: React.ReactNode, client = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  render(
    <QueryClientProvider client={client}>
      <AuthProvider>{ui}</AuthProvider>
    </QueryClientProvider>,
  );
  return client;
}

describe("AuthProvider + LoginForm", () => {
  it("kicks a signed-in user out with the locked notice and clears cached data", async () => {
    server.use(http.get(`${API}/users/me`, () => HttpResponse.json(LOCKED_BODY, { status: 403 })));
    const client = renderWithAuth(<><AuthProbe /><LoginForm /></>);
    await waitFor(() => expect(screen.getByTestId("auth")).toHaveTextContent(/^authenticated$/));
    client.setQueryData(["accounts", "list"], { items: ["cached"] });
    expect(screen.queryByText(LOCKED_NOTICE)).not.toBeInTheDocument();

    await act(async () => {
      await axiosInstance.get("/users/me").catch(() => undefined);
    });

    expect(screen.getByTestId("auth")).toHaveTextContent("unauthenticated:account-locked");
    expect(screen.getByText(LOCKED_NOTICE)).toBeInTheDocument();
    expect(client.getQueryData(["accounts", "list"])).toBeUndefined();
    expect(getAccessToken()).toBeNull();
  });

  it("keeps the locked notice when a request still in flight then ends the session as expired", async () => {
    // Sau khi bị khoá: token đã xoá → request chạy dở nhận 401 → refresh 401 (cookie đã bị xoá).
    server.use(
      http.get(`${API}/users/me`, () => HttpResponse.json(LOCKED_BODY, { status: 403 })),
      http.get(`${API}/courses`, () => HttpResponse.json({ error_code: "UNAUTHORIZED", message: "x" }, { status: 401 })),
    );
    renderWithAuth(<><AuthProbe /><LoginForm /></>);
    await waitFor(() => expect(screen.getByTestId("auth")).toHaveTextContent(/^authenticated$/));
    await act(async () => {
      await axiosInstance.get("/users/me").catch(() => undefined);
    });
    server.use(
      http.post(`${API}/auth/refresh-access-token`, () =>
        HttpResponse.json({ error_code: "SESSION_EXPIRED", message: "Phiên đăng nhập đã hết hạn" }, { status: 401 }),
      ),
    );
    await act(async () => {
      await axiosInstance.get("/courses").catch(() => undefined);
    });

    expect(screen.getByTestId("auth")).toHaveTextContent("unauthenticated:account-locked");
    expect(screen.getByText(LOCKED_NOTICE)).toBeInTheDocument();
  });

  it("clears the locked notice on the next login attempt and shows the generic error for a wrong password", async () => {
    server.use(
      http.post(`${API}/auth/refresh-access-token`, () => HttpResponse.json(LOCKED_BODY, { status: 403 })),
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json({ error_code: "INVALID_CREDENTIALS", message: "Email hoặc mật khẩu không đúng" }, { status: 401 }),
      ),
    );
    renderWithAuth(<><AuthProbe /><LoginForm /></>);
    expect(await screen.findByText(LOCKED_NOTICE)).toBeInTheDocument();
    const user = userEvent.setup();
    await user.type(document.querySelector<HTMLInputElement>('input[name="email"]')!, "6851071001@st.utc2.edu.vn");
    await user.type(document.querySelector<HTMLInputElement>('input[type="password"]')!, "sai-mat-khau");
    await user.click(screen.getByRole("button", { name: /đăng nhập/i }));

    expect(await screen.findByText("Email hoặc mật khẩu không đúng")).toBeInTheDocument();
    expect(screen.queryByText(LOCKED_NOTICE)).not.toBeInTheDocument();
    expect(screen.getByTestId("auth")).toHaveTextContent(/^unauthenticated$/);
  });

  it("shows the locked notice when a reload's refresh answers ACCOUNT_LOCKED", async () => {
    server.use(http.post(`${API}/auth/refresh-access-token`, () => HttpResponse.json(LOCKED_BODY, { status: 403 })));
    renderWithAuth(<><AuthProbe /><LoginForm /></>);
    await waitFor(() => expect(screen.getByTestId("auth")).toHaveTextContent("unauthenticated:account-locked"));
    expect(screen.getByText(LOCKED_NOTICE)).toBeInTheDocument();
  });

  it("shows no locked notice when the session simply expired", async () => {
    server.use(
      http.post(`${API}/auth/refresh-access-token`, () =>
        HttpResponse.json({ error_code: "SESSION_EXPIRED", message: "Phiên đăng nhập đã hết hạn" }, { status: 401 }),
      ),
    );
    renderWithAuth(<><AuthProbe /><LoginForm /></>);
    await waitFor(() => expect(screen.getByTestId("auth")).toHaveTextContent(/^unauthenticated$/));
    expect(screen.queryByText(LOCKED_NOTICE)).not.toBeInTheDocument();
  });

  it("logging in with the right password to a locked account shows the notice, not a wrong-password error", async () => {
    server.use(
      http.post(`${API}/auth/refresh-access-token`, () =>
        HttpResponse.json({ error_code: "SESSION_EXPIRED", message: "x" }, { status: 401 }),
      ),
      http.post(`${API}/auth/login`, () => HttpResponse.json(LOCKED_BODY, { status: 403 })),
    );
    renderWithAuth(<><AuthProbe /><LoginForm /></>);
    await waitFor(() => expect(screen.getByTestId("auth")).toHaveTextContent("unauthenticated"));
    const user = userEvent.setup();
    await user.type(document.querySelector<HTMLInputElement>('input[name="email"]')!, "6851071001@st.utc2.edu.vn");
    await user.type(document.querySelector<HTMLInputElement>('input[type="password"]')!, "6851071001");
    await user.click(screen.getByRole("button", { name: /đăng nhập/i }));

    expect(await screen.findByText(LOCKED_NOTICE)).toBeInTheDocument();
    expect(document.querySelector('input[type="password"]')).not.toHaveAttribute("aria-invalid", "true");
    expect(screen.queryByText("Tài khoản đã bị khoá")).not.toBeInTheDocument();
  });
});
