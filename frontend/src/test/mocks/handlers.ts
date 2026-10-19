import { http, HttpResponse } from "msw";
import { mockCoursesRaw } from "../fixtures/courses";

const API = "http://localhost:8000";

let accessTokenCounter = 0;

function makeMockJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" })).replace(/=+$/, "");
  const body = btoa(JSON.stringify(payload))
    .replace(/=+$/, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
  return `${header}.${body}.mock-sig`;
}

function makeAccessToken(userId: string, role: number): string {
  accessTokenCounter += 1;
  const now = Math.floor(Date.now() / 1000);
  return makeMockJwt({
    sub: userId,
    role,
    tv: accessTokenCounter,
    type: "access",
    iat: now,
    exp: now + 3600,
  });
}

const MOCK_USER = {
  user_id: "stu-001",
  role_id: 3,
  full_name: "Sinh viên Test",
  email: "student@utc2.edu.vn",
  must_change_password: false,
};

export const handlers = [
  // ─── Auth ───────────────────────────────────────────
  http.post(`${API}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };
    if (!body.email || !body.password) {
      return HttpResponse.json({ detail: "Email and password required" }, { status: 400 });
    }
    return HttpResponse.json({
      access_token: makeAccessToken(MOCK_USER.user_id, MOCK_USER.role_id),
      user: { ...MOCK_USER, email: body.email },
    });
  }),

  http.post(`${API}/auth/refresh-access-token`, () => {
    return HttpResponse.json({
      access_token: makeAccessToken(MOCK_USER.user_id, MOCK_USER.role_id),
    });
  }),

  http.post(`${API}/auth/logout`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // ─── Student dashboard ──────────────────────────────
  /**
   * BE trả về `courses: CourseResponseRaw[]` — FE sẽ gọi `toCourseSummary` để
   * map sang `CourseSummary`. Mock này phải trả RAW shape (course_id, course_name).
   */
  http.get(`${API}/students/:studentId/dashboard`, () => {
    return HttpResponse.json({
      total_classes: mockCoursesRaw.length,
      completed_problems: 12,
      total_problems: 30,
      average_score: 8.4,
      courses: mockCoursesRaw, // raw shape — FE tự transform
    });
  }),

  http.get(`${API}/api/v1/student/overview`, () => {
    return HttpResponse.json({
      total_classes: mockCoursesRaw.length,
      completed_problems: 12,
      total_problems: 30,
      average_score: 8.4,
      courses: mockCoursesRaw,
    });
  }),

  http.get(`${API}/api/v1/student/courses`, () => {
    return HttpResponse.json(mockCoursesRaw);
  }),

  http.get(`${API}/api/v1/courses/:id`, ({ params }) => {
    const course = mockCoursesRaw.find((c) => c.course_id === params.id);
    if (!course) {
      return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    }
    return HttpResponse.json(course);
  }),
];
