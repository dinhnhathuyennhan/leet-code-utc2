/**
 * Unit tests cho API endpoints (axios + MSW).
 * Verify:
 *  - Login success → trả JWT mock + user
 *  - Login 401 → throw ApiError có message tiếng Việt
 *  - getStudentOverview → trả courses[] đã transform (id/name khớp)
 *  - getStudentOverview 500 → throw ApiError
 *  - Network error → throw ApiError có isNetworkError = true
 */
import { describe, expect, it, afterEach } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { setAccessToken } from "@/lib/auth/token-store";

import { login } from "@/lib/api/endpoints/auth";
import { getStudentOverview } from "@/lib/api/endpoints/dashboard";
import { ApiError } from "@/lib/api/error";
import { mockCoursesRaw, mockCourses } from "@/test/fixtures/courses";

afterEach(() => {
  server.resetHandlers();
  setAccessToken(null);
});

describe("API: auth/login", () => {
  it("returns JWT access_token and user on success", async () => {
    const res = await login({ email: "stu@utc2.edu.vn", password: "secret" });
    expect(res.access_token.split(".")).toHaveLength(3);
    expect(res.user.email).toBe("stu@utc2.edu.vn");
    expect(res.user.role_id).toBe(3);
  });

  it("throws ApiError with Vietnamese message on 401", async () => {
    server.use(
      http.post("http://localhost:8000/auth/login", () => {
        return HttpResponse.json(
          { detail: "Email hoặc mật khẩu không chính xác" },
          { status: 401 },
        );
      }),
    );

    await expect(
      login({ email: "wrong@utc2.edu.vn", password: "wrong" }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      detail: "Email hoặc mật khẩu không chính xác",
    });
  });
});

describe("API: getStudentOverview", () => {
  it("transforms raw course_id → id and returns courses array", async () => {
    setAccessToken("any-token");
    const data = await getStudentOverview("stu-001");

    expect(data.courses).toHaveLength(mockCoursesRaw.length);
    expect(data.courses[0]).toMatchObject({
      id: "CS101",
      code: "CS101",
      name: "Nhập môn lập trình",
      total_number_student: 60,
    });
  });

  it("matches the CourseSummary shape (transformer output)", async () => {
    setAccessToken("any-token");
    const data = await getStudentOverview("stu-001");
    expect(data.courses).toEqual(mockCourses);
  });

  it("passes through stats fields from the API response", async () => {
    setAccessToken("any-token");
    const data = await getStudentOverview("stu-001");
    expect(data).toMatchObject({
      total_classes: mockCoursesRaw.length,
      completed_problems: 12,
      total_problems: 30,
      average_score: 8.4,
    });
  });
});

describe("API: error handling", () => {
  it("wraps 500 into ApiError with default message", async () => {
    server.use(
      http.get("http://localhost:8000/students/stu-001/dashboard", () => {
        return HttpResponse.json({ detail: "boom" }, { status: 500 });
      }),
    );
    setAccessToken("any-token");

    await expect(getStudentOverview("stu-001")).rejects.toBeInstanceOf(ApiError);
  });

  it("throws ApiError with isNetworkError = true on network failure", async () => {
    server.use(
      http.get("http://localhost:8000/students/stu-001/dashboard", () => {
        return HttpResponse.error();
      }),
    );
    setAccessToken("any-token");

    await expect(getStudentOverview("stu-001")).rejects.toMatchObject({
      isNetworkError: true,
      status: 0,
    });
  });
});
