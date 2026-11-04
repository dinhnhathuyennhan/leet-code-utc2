import { afterEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { setAccessToken } from "@/lib/auth/token-store";
import axiosInstance from "@/lib/axios";
import {
  addAdminClassEnrollment, adminCourseUrl, adminProblemUrl, deleteAdminEnrollment,
  getAdminCourses, getAdminProblems, saveAdminLesson, saveAdminSubmission, uploadAdminTestcases,
} from "./admin-management";

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

  it("uses the backend bulk class-enrollment route", async () => {
    server.use(http.post(`${API}/courses/:id/enrollments/class`, async ({ request, params }) => {
      expect(params.id).toBe("JAVA#01");
      expect(await request.json()).toEqual({ class_id: "CQ.67.CNTT" });
      return HttpResponse.json({ added_count: 4, skipped_count: 2 }, { status: 201 });
    }));
    expect(await addAdminClassEnrollment("JAVA#01", "CQ.67.CNTT")).toEqual({ added_count: 4, skipped_count: 2 });
  });

  it("preserves the complete student ID when removing an enrollment", async () => {
    let requested = false;
    server.use(http.delete(`${API}/courses/:id/enrollments/:studentId`, ({ params }) => {
      expect(params.studentId).toBe("sv#02");
      requested = true;
      return new HttpResponse(null, { status: 204 });
    }));
    await deleteAdminEnrollment("JAVA01", "sv#02");
    expect(requested).toBe(true);
  });

  it("sends calendar dates rather than timestamps for a lesson", async () => {
    server.use(http.post(`${API}/courses/:id/lessons`, async ({ request }) => {
      expect(await request.json()).toEqual({ lesson_name: "Mảng", start_date: "2026-10-01", end_date: "2026-10-31", problem_ids: [] });
      return HttpResponse.json({ course_id: "JAVA01" });
    }));
    await saveAdminLesson("JAVA01", { lesson_name: "Mảng", start_date: "2026-10-01", end_date: "2026-10-31", problem_ids: [] });
  });

  it("keeps testcase FormData intact through the instance's default JSON transform", async () => {
    const previousAdapter = axiosInstance.defaults.adapter;
    const file = new File(["[]"], "tests.json", { type: "application/json" });
    axiosInstance.defaults.adapter = async (config) => {
      expect(config.headers.getContentType()).toBe("multipart/form-data");
      expect(config.data).toBeInstanceOf(FormData);
      expect((config.data as FormData).get("file")).toBe(file);
      return { data: { id: 2, testcases: [{ input: [[1, 2]], expected_output: 3 }] }, status: 200, statusText: "OK", headers: {}, config };
    };
    try {
      const response = await uploadAdminTestcases("JAVA01", "1", "2", file);
      expect(response.testcases[0].input).toEqual([[1, 2]]);
    } finally {
      axiosInstance.defaults.adapter = previousAdapter;
    }
  });

  it("preserves null to remove a manual grade override", async () => {
    server.use(http.patch(`${API}/submissions/42`, async ({ request }) => {
      expect(await request.json()).toEqual({ feedback: "Đã kiểm tra", status: "accepted", manual_score: null });
      return HttpResponse.json({ id: 42, manual_score: null });
    }));
    expect(await saveAdminSubmission("42", { feedback: "Đã kiểm tra", status: "accepted", manual_score: null })).toMatchObject({ id: 42, manual_score: null });
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
