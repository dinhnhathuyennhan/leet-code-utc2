// vitest.setup.ts
// QUAN TRỌNG: set env TRƯỚC khi import bất cứ module nào dùng process.env
process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";

import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "./src/test/mocks/server";

// Polyfill cho Next.js Link
import "next/link";

// Khởi động MSW
beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());

// Stub matchMedia (sonner + nhiều UI lib dùng)
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Node 25+ tự định nghĩa `localStorage` toàn cục; khi không truyền `--localstorage-file`
// nó là undefined và che mất localStorage của jsdom → thay bằng Storage trong bộ nhớ.
if (typeof globalThis.localStorage?.clear !== "function") {
  class MemoryStorage implements Storage {
    private store = new Map<string, string>();
    get length() { return this.store.size; }
    clear() { this.store.clear(); }
    getItem(key: string) { return this.store.get(String(key)) ?? null; }
    key(index: number) { return Array.from(this.store.keys())[index] ?? null; }
    removeItem(key: string) { this.store.delete(String(key)); }
    setItem(key: string, value: string) { this.store.set(String(key), String(value)); }
  }
  for (const name of ["localStorage", "sessionStorage"] as const) {
    Object.defineProperty(globalThis, name, { configurable: true, writable: true, value: new MemoryStorage() });
  }
}

// Stub IntersectionObserver
class IOStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-expect-error - chỉ stub cho môi trường test
globalThis.IntersectionObserver = IOStub;
