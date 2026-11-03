/**
 * E2E: giao vien tao lop + bai tap + sinh vien moi -> sinh vien dang nhap tren UI,
 * lam bai SAI roi lam bai DUNG (Playwright + Judge0 that).
 *
 * Chay (tu thu muc frontend/):  npm run test:e2e-create
 * Yeu cau: backend :8000, frontend :3000, judge0 :2358 deu dang chay.
 * Du lieu tao ra co tien to "E2E" + timestamp (khong dung vao du lieu seed).
 */

import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const API = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";
const FRONTEND = process.env.UI_FRONTEND_URL ?? "http://localhost:3000";
const TEACHER_EMAIL = process.env.E2E_TEACHER_EMAIL ?? "1111111117@st.utc2.edu.vn";
const TEACHER_PASSWORD = process.env.E2E_TEACHER_PASSWORD ?? "Password@123";
const CLASS_ID = process.env.E2E_CLASS_ID ?? "CQ.62.CNTT";
const NEW_PASSWORD = "E2eNew@2026";

const here = dirname(fileURLToPath(import.meta.url));
const SHOTS = join(here, "..", "..", "docs", "ui-shots", "create-and-solve");
mkdirSync(SHOTS, { recursive: true });

const stamp = Date.now().toString().slice(-8);
const STUDENT_ID = `99${stamp}`;
const STUDENT_EMAIL = `${STUDENT_ID}@st.utc2.edu.vn`;
const COURSE_ID = `E2E${stamp}`;
const PROBLEM_TITLE = `E2E Tong hai so ${stamp}`;

let passed = 0;
let failed = 0;
const consoleErrors = [];

function check(name, condition, detail = "") {
  if (condition) {
    passed += 1;
    console.log(`PASS ${name.padEnd(54)} ${detail}`);
  } else {
    failed += 1;
    console.log(`FAIL ${name.padEnd(54)} ${detail}`);
  }
}

async function api(method, path, { token, body } = {}) {
  const response = await fetch(`${API}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let data = null;
  try {
    data = await response.json();
  } catch {
    /* body rong */
  }
  return { status: response.status, data };
}

const isoDate = (offsetDays) => new Date(Date.now() + offsetDays * 86_400_000).toISOString();
const dateOnly = (offsetDays) => isoDate(offsetDays).slice(0, 10);

/** Giao vien tao sinh vien, lop, buoi hoc, bai tap qua API. Tra ve id can dung cho UI. */
async function setupAsTeacher() {
  console.log("--- PHAN 1: GIAO VIEN TAO DU LIEU (API) ---");
  const login = await api("POST", "/auth/login", {
    body: { email: TEACHER_EMAIL, password: TEACHER_PASSWORD },
  });
  check("giao vien dang nhap", login.status === 200, `${TEACHER_EMAIL} status=${login.status}`);
  if (login.status !== 200) throw new Error("Giao vien khong dang nhap duoc");
  const token = login.data.access_token;

  const student = await api("POST", "/students", {
    token,
    body: {
      user_id: STUDENT_ID,
      full_name: `Sinh Vien E2E ${stamp}`,
      date_of_birth: "2004-05-06",
      email: STUDENT_EMAIL,
      class_id: CLASS_ID,
    },
  });
  check("tao tai khoan sinh vien", student.status === 201, `${STUDENT_EMAIL} status=${student.status}`);

  const course = await api("POST", "/courses", {
    token,
    body: {
      course_id: COURSE_ID,
      course_name: `Lop E2E ${stamp}`,
      term: "HK1-2026",
      start_date: isoDate(-1),
      end_date: isoDate(60),
    },
  });
  check("tao lop hoc phan", course.status === 201, `${COURSE_ID} status=${course.status}`);

  const enroll = await api("POST", `/courses/${COURSE_ID}/enrollments`, {
    token,
    body: { student_id: STUDENT_ID },
  });
  check("them sinh vien vao lop", [200, 201].includes(enroll.status), `status=${enroll.status}`);

  const problem = await api("POST", "/problems", {
    token,
    body: {
      title: PROBLEM_TITLE,
      function_name: "sum_two",
      description: "Viet ham sum_two(a, b) tra ve tong cua hai so nguyen a va b.",
      constraints: "-10^9 <= a, b <= 10^9",
      level: "easy",
      time_limit_seconds: 2,
      starter_codes: {
        python: "def sum_two(a, b):\n    pass\n",
        c: "int sum_two(int a, int b) {\n    return 0;\n}\n",
        cpp: "int sum_two(int a, int b) {\n    return 0;\n}\n",
        java: "class Solution {\n    int sum_two(int a, int b) {\n        return 0;\n    }\n}\n",
      },
      start_datetime: isoDate(-1),
      end_datetime: isoDate(30),
      testcases: [
        { input: [1, 2], expected_output: 3, is_sample: true },
        { input: [10, -4], expected_output: 6, is_sample: true },
        { input: [0, 0], expected_output: 0 },
        { input: [123456, 654321], expected_output: 777777 },
      ],
    },
  });
  check("tao bai tap (ngan hang)", problem.status === 201, `status=${problem.status} ${problem.status !== 201 ? JSON.stringify(problem.data) : ""}`);
  const bankProblemId = problem.data?.id ?? problem.data?.problem_id;

  const lesson = await api("POST", `/courses/${COURSE_ID}/lessons`, {
    token,
    body: {
      lesson_name: "Buoi E2E: Tong hai so",
      start_date: dateOnly(-1),
      end_date: dateOnly(14),
      problem_ids: [bankProblemId],
    },
  });
  check("tao buoi hoc + gan bai tap", [200, 201].includes(lesson.status), `status=${lesson.status} ${lesson.status >= 300 ? JSON.stringify(lesson.data) : ""}`);
  const session = (lesson.data?.sessions ?? []).find((s) => s.title === "Buoi E2E: Tong hai so");
  const lessonProblem = session?.problems?.[0];
  check("buoi hoc co bai tap vua gan", Boolean(lessonProblem), `lesson=${session?.id} problem=${lessonProblem?.id}`);
  if (!session || !lessonProblem) throw new Error("Khong tao duoc bai tap trong buoi hoc");
  return { lessonId: session.id, problemId: lessonProblem.id };
}

/** Sinh vien moi dang nhap tren UI (doi mat khau lan dau), vao lop, lam bai SAI roi DUNG. */
async function solveAsStudent({ lessonId, problemId }) {
  console.log("--- PHAN 2: SINH VIEN MOI LAM BAI (UI) ---");
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  const page = await context.newPage();

  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (!text.includes("401") && !text.includes("Failed to load resource")) consoleErrors.push(text);
  });
  page.on("pageerror", (error) => consoleErrors.push(`pageerror: ${error.message}`));

  const shot = (name) => page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true });
  const bodyText = () => page.locator("body").innerText();

  async function open(path) {
    await page.goto(`${FRONTEND}${path}`, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page
      .waitForFunction(() => document.body && document.body.innerText.trim().length > 0, null, { timeout: 20000 })
      .catch(() => {});
    await page.waitForTimeout(1200);
  }

  /** Cho Judge0 cham xong: hien "Ket qua bai nop" va het dong "Dang cham bai...". */
  async function waitGraded() {
    await page.waitForSelector("text=Kết quả bài nộp", { timeout: 90000 });
    await page
      .waitForFunction(() => !document.body.innerText.includes("Đang chấm bài, vui lòng chờ"), null, { timeout: 90000 })
      .catch(() => {});
    await page.waitForTimeout(800);
  }

  /**
   * Nop bai va cho dung lan nop nay duoc cham xong.
   * Panel ket qua cua lan nop truoc van con tren trang, nen phai bat submission_id
   * moi tu response POST roi cho response /result cua chinh id do co trang thai cuoi.
   */
  async function submit(code) {
    const editor = page.locator('textarea[aria-label="Mã nguồn bài nộp"]');
    await editor.fill(code);
    const submitted = page.waitForResponse(
      (r) => r.request().method() === "POST" && /\/problems\/\d+\/submissions$/.test(r.url()),
      { timeout: 30000 },
    );
    await page.locator('button:has-text("Nộp bài")').first().click();
    const submitResponse = await submitted;
    const submissionId = (await submitResponse.json()).submission_id;
    await page.waitForResponse(
      async (r) => {
        if (!r.url().includes(`/submissions/${submissionId}/result`) || r.status() !== 200) return false;
        const data = await r.json().catch(() => ({}));
        return !["pending", "processing"].includes(data.status);
      },
      { timeout: 90000 },
    );
    await waitGraded();
    return bodyText();
  }

  try {
    // 1. Dang nhap bang mat khau tam (= MSSV), bi buoc doi mat khau
    await open("/login");
    await page.fill('input[type="email"]', STUDENT_EMAIL);
    await page.fill('input[type="password"]', STUDENT_ID);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(student|change-password)/, { timeout: 20000 }).catch(() => {});
    check("sinh vien moi dang nhap duoc (mat khau tam = MSSV)", /\/(student|change-password)/.test(page.url()), page.url());
    check("bi buoc doi mat khau lan dau", page.url().includes("/change-password"), page.url());
    await shot("01-first-login");

    // 2. Doi mat khau
    if (page.url().includes("/change-password")) {
      const fields = page.locator('input[type="password"]');
      await fields.nth(0).fill(STUDENT_ID);
      await fields.nth(1).fill(NEW_PASSWORD);
      await fields.nth(2).fill(NEW_PASSWORD);
      await page.locator('button[type="submit"]').click();
      await page.waitForURL(/\/student\//, { timeout: 25000 }).catch(() => {});
      check("doi mat khau xong -> vao trang sinh vien", page.url().includes("/student/"), page.url());
    }
    await page.waitForTimeout(1500);
    await shot("02-student-home");

    // 3. Thay lop vua tao trong danh sach lop
    await open("/student/classes");
    const classesText = await bodyText();
    check("danh sach lop co lop vua tao", classesText.includes(`Lop E2E ${stamp}`), `Lop E2E ${stamp}`);
    await shot("03-classes");

    // 4. Vao lop -> thay buoi hoc va bai tap
    await page.locator(`a[href="/student/classes/${COURSE_ID}"]`).first().click();
    await page.waitForURL(new RegExp(`/student/classes/${COURSE_ID}`), { timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(2000);
    const classText = await bodyText();
    check("trang lop co buoi hoc vua tao", classText.includes("Buoi E2E"), "");
    check("trang lop co bai tap vua tao", classText.includes(PROBLEM_TITLE), PROBLEM_TITLE);
    await shot("04-class-detail");

    // 5. Mo bai tap
    const assignmentLink = page.locator(`a[href="/student/classes/${COURSE_ID}/assignments/${problemId}"]`).first();
    check("co link toi bai tap", (await assignmentLink.count()) > 0, `problem=${problemId} lesson=${lessonId}`);
    if ((await assignmentLink.count()) > 0) await assignmentLink.click();
    else await open(`/student/classes/${COURSE_ID}/assignments/${problemId}`);
    await page.waitForURL(new RegExp(`/assignments/${problemId}`), { timeout: 20000 }).catch(() => {});
    await page.waitForSelector('textarea[aria-label="Mã nguồn bài nộp"]', { timeout: 20000 }).catch(() => {});
    const assignText = await bodyText();
    check("trang bai tap co de bai", assignText.includes("sum_two"), "");
    check("co testcase mau", assignText.includes("Testcase mẫu") || assignText.includes("Sample"), "");
    await shot("05-assignment");

    const editor = page.locator('textarea[aria-label="Mã nguồn bài nộp"]');
    check("editor nap ma mau Python", (await editor.inputValue()).includes("def sum_two"), "");

    // 6. LAM SAI: tra ve a - b
    const wrongText = await submit("def sum_two(a, b):\n    return a - b\n");
    check("bai sai -> hien 'Sai ket qua'", wrongText.includes("Sai kết quả"), "");
    check("bai sai -> khong hien 'Dat' o trang thai chinh", !/Trạng thái.*Đạt/s.test(wrongText), "");
    check("bai sai -> co bang testcase", /Test\s*#?\s*1/i.test(wrongText), "");
    check("bai sai -> diem < 10", !wrongText.includes("10.0/10"), "");
    await shot("06-result-wrong");

    // 7. LAM SAI KIEU KHAC: loi cu phap -> Loi bien dich
    const syntaxText = await submit("def sum_two(a, b)\n    return a + b\n");
    check("loi cu phap -> hien 'Loi bien dich'", syntaxText.includes("Lỗi biên dịch"), "");
    await shot("07-result-compile-error");

    // 8. LAM DUNG
    const rightText = await submit("def sum_two(a, b):\n    return a + b\n");
    check("bai dung -> hien 'Dat'", rightText.includes("Đạt"), "");
    check("bai dung -> 4/4 testcase", rightText.includes("4/4"), "");
    check("bai dung -> diem 10/10", rightText.includes("10.0"), "");
    check("bai dung -> khong con 'Sai ket qua' o ket qua moi", !/Sai kết quả/.test(rightText.split("Kết quả bài nộp")[1] ?? ""), "");
    await shot("08-result-accepted");

    // 9. Lich su nop bai: du 3 lan nop
    await open("/student/history");
    const history = await bodyText();
    check("lich su co bai vua nop", history.includes(PROBLEM_TITLE), "");
    check("lich su co trang thai Dat", history.includes("Đạt"), "");
    check("lich su co trang thai Sai ket qua", history.includes("Sai kết quả"), "");
    check("lich su co trang thai Loi bien dich", history.includes("Lỗi biên dịch"), "");
    await shot("09-history");

    check("khong co loi runtime trong console", consoleErrors.length === 0, consoleErrors.slice(0, 2).join(" | "));
  } finally {
    await browser.close();
  }
}

/** Giao vien xem lai bai nop cua sinh vien moi (xac nhan du lieu hien o phia giao vien). */
async function verifyAsTeacher() {
  console.log("--- PHAN 3: GIAO VIEN KIEM TRA LAI (API) ---");
  const login = await api("POST", "/auth/login", {
    body: { email: TEACHER_EMAIL, password: TEACHER_PASSWORD },
  });
  const token = login.data?.access_token;
  const pending = await api("GET", `/submissions/pending?filter=all&limit=100&search=${encodeURIComponent(STUDENT_ID)}`, { token });
  const items = pending.data?.items ?? [];
  const mine = items.filter((item) => JSON.stringify(item).includes(STUDENT_ID) || JSON.stringify(item).includes(COURSE_ID));
  check("giao vien thay bai nop cua sinh vien moi", mine.length >= 2, `${mine.length} bai (sai/loi, bai dung tu dong cham)`);

  const wrongRight = await api("GET", `/courses/${COURSE_ID}`, { token });
  check("giao vien xem duoc lop vua tao", wrongRight.status === 200, `status=${wrongRight.status}`);
}

async function main() {
  console.log("=".repeat(100));
  console.log(`E2E TAO LOP + BAI TAP + SINH VIEN LAM BAI   API=${API}   UI=${FRONTEND}`);
  console.log(`Du lieu: sinh vien=${STUDENT_EMAIL}  lop=${COURSE_ID}`);
  console.log("=".repeat(100));
  try {
    const ids = await setupAsTeacher();
    await solveAsStudent(ids);
    await verifyAsTeacher();
  } catch (error) {
    failed += 1;
    console.log(`FAIL exception: ${error.message}`);
  }
  console.log("=".repeat(100));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  console.log(`Screenshots: ${SHOTS}`);
  console.log("=".repeat(100));
  process.exit(failed > 0 ? 1 : 0);
}

main();
