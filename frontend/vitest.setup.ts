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

// Stub IntersectionObserver
class IOStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-expect-error - chỉ stub cho môi trường test
globalThis.IntersectionObserver = IOStub;
