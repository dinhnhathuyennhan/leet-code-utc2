import { afterEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { setAccessToken } from "@/lib/auth/token-store";
import { adminCourseUrl, adminProblemUrl, getAdminCourses, getAdminProblems } from "./admin-management";

const API = "http://localhost:8000";
afterEach(() => setAccessToken(null));

describe("Admin API contracts", () => {
  it("encodes reserved characters in course and problem paths", () => {
    expect(adminCourseUrl("Lớp #1")).toBe("/courses/L%E1%BB%9Bp%20%231");
    expect(adminProblemUrl("JAVA#02", "5", "8")).toBe("/courses/JAVA%2302/lessons/5/problems/8");
  });

  it("requests real courses with the signed-in token", async () => {
    setAccessToken("admin-token");
    server.use(http.get(`${API}/courses`, ({ request }) => {
      expect(request.headers.get("Authorization")).toBe("Bearer admin-token");
      return HttpResponse.json([{ course_id: "JAVA01", created_by: "teacher-1", sessions: [] }]);
    }));
    expect(await getAdminCourses()).toMatchObject([{ course_id: "JAVA01", created_by: "teacher-1" }]);
  });

  it("passes problem search and pagination to the existing endpoint", async () => {
    server.use(http.get(`${API}/problems`, ({ request }) => {
      const url = new URL(request.url);
      expect(url.searchParams.get("q")).toBe("mảng");
      expect(url.searchParams.get("level")).toBe("easy");
      expect(url.searchParams.get("page")).toBe("2");
      return HttpResponse.json({ items: [], total: 0, page: 2, page_size: 20 });
    }));
    expect((await getAdminProblems({ q: "mảng", level: "easy", page: 2 })).items).toEqual([]);
  });
});
