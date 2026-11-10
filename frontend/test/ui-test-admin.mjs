/**
 * Test GIAO DIỆN thật cho luồng quản trị viên (Playwright + Chromium).
 *
 * Chạy (từ thư mục frontend/):  npm run test:ui-admin
 * Yêu cầu:
 *  - backend :8000, frontend :3000, Judge0 và Ollama đều đang chạy.
 *  - Đã seed dữ liệu demo (tools/seed_demo_data.py).
 *  - Có tài khoản admin (role_id=1). Seed demo KHÔNG tạo admin, nên phải tạo sẵn
 *    rồi truyền qua UI_ADMIN_EMAIL / UI_ADMIN_PASSWORD nếu khác mặc định.
 *
 * Dữ liệu tạo ra mang mã theo timestamp và KHÔNG tự xoá hết được (hệ thống không
 * có API xoá tài khoản/lớp học phần). Chỉ chạy trên DB local.
 * Bài nộp seed bị sửa ở bước đánh giá được khôi phục ngay trong `finally`.
 */

import { chromium } from "playwright";
import { mkdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const FRONTEND = process.env.UI_FRONTEND_URL ?? "http://localhost:3000";
const API = process.env.UI_API_URL ?? "http://localhost:8000";
const ADMIN_EMAIL = process.env.UI_ADMIN_EMAIL ?? "admin.demo@st.utc2.edu.vn";
const ADMIN_PASSWORD = process.env.UI_ADMIN_PASSWORD ?? "Password@123";
const SEED_PASSWORD = process.env.UI_SEED_PASSWORD ?? "Password@123";
const STUDENT_EMAIL = process.env.UI_STUDENT_EMAIL ?? "6751071001@st.utc2.edu.vn";
const TEACHER_EMAIL = process.env.UI_TEACHER_EMAIL ?? "1111111117@st.utc2.edu.vn";
const SEED_CLASS_ID = process.env.UI_CLASS_ID ?? "CQ.67.CNTT";
const SEED_COURSE_ID = process.env.UI_COURSE_ID ?? "DEMO101-2026A";
const SEED_PROBLEM_TITLE = "Tổng hai số";

const here = dirname(fileURLToPath(import.meta.url));
const SHOTS = join(here, "..", "..", "docs", "ui-shots", "admin");
mkdirSync(SHOTS, { recursive: true });

const stamp = Date.now().toString().slice(-8);
const NEW_STUDENT_CODE = `97${stamp}`;
const NEW_STUDENT_EMAIL = `${NEW_STUDENT_CODE}@st.utc2.edu.vn`;
const NEW_STUDENT_NAME = `Sinh Vien Admin ${stamp}`;
const NEW_TEACHER_EMAIL = `gvadmin${stamp}@st.utc2.edu.vn`;
const NEW_TEACHER_NAME = `Giang Vien Admin ${stamp}`;
const NEW_COURSE_ID = `ADM${stamp}`;
const NEW_COURSE_NAME = `Lop Admin ${stamp}`;
const NEW_LESSON_NAME = `Buoi Admin ${stamp}`;
const NEW_PROBLEM_TITLE = `Bai Admin ${stamp}`;
const NEW_CLASS_DEPARTMENT = `ADM${stamp}`;
const NEW_CLASS_NUMBER = String(Number(stamp.slice(-5)) + 1);

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const MSSV_PATTERN = /^\d{10}$/;
const ERROR_TEXT = /Đã xảy ra lỗi|Internal Server Error|Application error/i;

let passed = 0;
let failed = 0;
let skipped = 0;
const consoleErrors = [];

function check(name, condition, detail = "") {
  if (condition) passed += 1;
  else failed += 1;
  console.log(`${condition ? "PASS" : "FAIL"} ${name.padEnd(62)} ${detail}`);
}

function skip(name, reason) {
  skipped += 1;
  console.log(`SKIP ${name.padEnd(62)} ${reason}`);
}

const isoDate = (offsetDays) => new Date(Date.now() + offsetDays * 86_400_000).toISOString();
const dateOnly = (offsetDays) => isoDate(offsetDays).slice(0, 10);
const dateTimeLocal = (offsetDays) => isoDate(offsetDays).slice(0, 19);

/** Gọi API trực tiếp bằng fetch: không dùng chung cookie với trình duyệt. */
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
    /* body rỗng */
  }
  return { status: response.status, data };
}

async function apiLogin(email, password) {
  const { status, data } = await api("POST", "/auth/login", { body: { email, password } });
  return { status, token: data?.access_token ?? null, user: data?.user ?? null };
}

const countOf = (data) => (Array.isArray(data) ? data.length : data?.total);

async function main() {
  console.log("=".repeat(100));
  console.log(`UI TEST ADMIN  ->  ${FRONTEND}   (API ${API})`);
  console.log(`Du lieu test: sinh vien=${NEW_STUDENT_CODE}  giang vien=${NEW_TEACHER_EMAIL}  lop=${NEW_COURSE_ID}`);
  console.log("=".repeat(100));

  const preflight = await apiLogin(ADMIN_EMAIL, ADMIN_PASSWORD);
  const me = preflight.token ? await api("GET", "/users/me", { token: preflight.token }) : null;
  if (me?.data?.role_id !== 1) {
    console.log(`FAIL Khong dang nhap duoc admin ${ADMIN_EMAIL} (status=${preflight.status}, role=${me?.data?.role_id}).`);
    console.log("     Tao tai khoan admin tren DB local roi dat UI_ADMIN_EMAIL / UI_ADMIN_PASSWORD.");
    process.exit(1);
  }
  const adminToken = preflight.token;
  const adminName = me.data.full_name;

  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "vi-VN", acceptDownloads: true });
  const page = await context.newPage();

  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (!text.includes("401") && !text.includes("Failed to load resource")) consoleErrors.push(text);
  });
  page.on("pageerror", (error) => consoleErrors.push(`pageerror: ${error.message}`));

  /** Ghi lại request ghi dữ liệu để xác nhận form không hợp lệ KHÔNG gọi API. */
  const writes = [];
  page.on("request", (request) => {
    if (request.url().startsWith(API) && ["POST", "PATCH", "PUT", "DELETE"].includes(request.method())) {
      if (!/\/auth\//.test(request.url())) writes.push(`${request.method()} ${request.url()}`);
    }
  });

  const shot = (name) => page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true });
  const body = () => page.locator("body").innerText();
  const heading = () => page.locator("h1").first().innerText();
  const dialog = () => page.getByRole("dialog");

  async function open(path) {
    await page.goto(`${FRONTEND}${path}`, { waitUntil: "domcontentloaded", timeout: 45_000 });
    await page.waitForFunction(() => document.querySelector("h1") !== null, null, { timeout: 25_000 }).catch(() => {});
    await page.waitForTimeout(1000);
  }

  /** Toast của sonner; trả về false nếu không thấy trong thời gian chờ. */
  const toast = (text, timeout = 10_000) =>
    page.locator("[data-sonner-toast]").filter({ hasText: text }).first()
      .waitFor({ timeout }).then(() => true).catch(() => false);

  /** Giá trị của thẻ số liệu; chờ tới khi hết placeholder "—". */
  async function metric(card) {
    const value = card.locator("p.text-3xl").first();
    for (let attempt = 0; attempt < 30; attempt += 1) {
      const text = (await value.textContent().catch(() => null))?.trim();
      if (text && text !== "—") return text;
      await page.waitForTimeout(300);
    }
    return "—";
  }
  const adminMetric = (label) => metric(page.locator("article").filter({ hasText: label }).first());

  /** Bấm nút và chờ response của API khớp `pattern`; trả về status (null nếu không có request). */
  async function submitAndStatus(pattern, method, action, timeout = 20_000) {
    const waiting = page
      .waitForResponse((r) => r.request().method() === method && pattern.test(r.url()), { timeout })
      .catch(() => null);
    await action();
    const response = await waiting;
    return response ? response.status() : null;
  }

  /** Thao tác trên form không hợp lệ: trả về số request ghi phát sinh. */
  async function writesDuring(action) {
    const before = writes.length;
    await action();
    await page.waitForTimeout(700);
    return writes.length - before;
  }

  /** Chạy một nhóm kiểm tra; exception chỉ làm hỏng nhóm đó, không dừng cả lượt. */
  async function section(name, fn) {
    console.log(`\n--- ${name} ---`);
    try {
      await fn();
    } catch (error) {
      check(`${name}: khong co exception`, false, String(error.message).split("\n")[0]);
      await shot(`99-${name.replace(/[^a-zA-Z0-9]+/g, "-").toLowerCase()}`).catch(() => {});
    }
  }

  async function uiLogin(targetPage, email, password, target) {
    await targetPage.goto(`${FRONTEND}/login`, { waitUntil: "domcontentloaded", timeout: 45_000 });
    await targetPage.locator('input[type="email"]').waitFor({ timeout: 25_000 });
    await targetPage.fill('input[type="email"]', email);
    await targetPage.fill('input[type="password"]', password);
    await targetPage.click('button[type="submit"]');
    await targetPage.waitForURL(target, { timeout: 25_000 });
  }

  /** Mở trang bằng một vai trò khác và xác nhận thấy màn hình 403. */
  async function isForbidden(targetPage, path) {
    await targetPage.goto(`${FRONTEND}${path}`, { waitUntil: "domcontentloaded", timeout: 45_000 });
    return targetPage.getByText("Bạn không có quyền truy cập trang này.").first()
      .waitFor({ timeout: 15_000 }).then(() => true).catch(() => false);
  }

  /** Tìm dòng tài khoản qua các trang vì ô tìm kiếm chỉ lọc trang hiện tại. */
  async function findAccountRow(needle, roleFilter) {
    await page.getByLabel("Lọc tài khoản theo vai trò").selectOption(roleFilter);
    await page.waitForTimeout(1000);
    for (let attempt = 0; attempt < 30; attempt += 1) {
      const row = page.locator("tbody tr").filter({ hasText: needle });
      if ((await row.count()) > 0) return row.first();
      const next = page.getByRole("button", { name: "Sau", exact: true });
      if (await next.isDisabled()) return null;
      await next.click();
      await page.waitForTimeout(800);
    }
    return null;
  }

  const created = { student: false, teacher: false, course: false, lesson: false, problem: false };

  try {
    // ── 1. Phân quyền ─────────────────────────────────────────────────
    await section("Phan quyen", async () => {
      const guestContext = await browser.newContext({ locale: "vi-VN" });
      const guest = await guestContext.newPage();
      await guest.goto(`${FRONTEND}/admin/dashboard`, { waitUntil: "domcontentloaded", timeout: 45_000 });
      const redirected = await guest.waitForURL(/\/login/, { timeout: 20_000 }).then(() => true).catch(() => false);
      check("chua dang nhap -> /admin chuyen ve /login", redirected, guest.url());
      await guestContext.close();

      const studentContext = await browser.newContext({ locale: "vi-VN" });
      const studentPage = await studentContext.newPage();
      await uiLogin(studentPage, STUDENT_EMAIL, SEED_PASSWORD, /\/student/);
      check("sinh vien mo /admin/accounts -> 403", await isForbidden(studentPage, "/admin/accounts"));
      await studentContext.close();

      const teacherContext = await browser.newContext({ locale: "vi-VN" });
      const teacherPage = await teacherContext.newPage();
      await uiLogin(teacherPage, TEACHER_EMAIL, SEED_PASSWORD, /\/teacher/);
      check("giang vien mo /admin/dashboard -> 403", await isForbidden(teacherPage, "/admin/dashboard"));
      await teacherContext.close();

      const student = await apiLogin(STUDENT_EMAIL, SEED_PASSWORD);
      const teacher = await apiLogin(TEACHER_EMAIL, SEED_PASSWORD);
      const anonymous = await api("GET", "/users");
      check("API: khong token GET /users -> 401", anonymous.status === 401, String(anonymous.status));
      const asStudent = await api("GET", "/users", { token: student.token });
      check("API: sinh vien GET /users -> 403", asStudent.status === 403, String(asStudent.status));
      const teacherCreate = await api("POST", "/teachers", {
        token: teacher.token,
        body: { full_name: "Khong Duoc Tao", email: `denied${stamp}@st.utc2.edu.vn` },
      });
      check("API: giang vien POST /teachers -> 403", teacherCreate.status === 403, String(teacherCreate.status));
      const teacherDelete = await api("DELETE", `/classes/KHONG-TON-TAI-${stamp}`, { token: teacher.token });
      check("API: giang vien DELETE /classes -> 403", teacherDelete.status === 403, String(teacherDelete.status));

      await uiLogin(page, ADMIN_EMAIL, ADMIN_PASSWORD, /\/admin\/dashboard/);
      check("admin dang nhap -> /admin/dashboard", page.url().includes("/admin/dashboard"), page.url());
      check("admin mo /student/dashboard -> 403", await isForbidden(page, "/student/dashboard"));
      check("admin mo /teacher -> 403", await isForbidden(page, "/teacher"));
    });

    // ── 2. Tổng quan + điều hướng ─────────────────────────────────────
    await section("Tong quan", async () => {
      await open("/admin/dashboard");
      check("dashboard co tieu de", (await heading()).includes("Tổng quan quản trị"), await heading());
      check("dashboard chao dung ten admin", (await body()).includes(adminName), adminName);

      const users = await api("GET", "/users?page=1&page_size=1", { token: adminToken });
      const courses = await api("GET", "/courses", { token: adminToken });
      const classes = await api("GET", "/classes", { token: adminToken });
      const pending = await api("GET", "/submissions/pending?filter=all&limit=6", { token: adminToken });
      for (const [label, expected] of [
        ["Tài khoản", countOf(users.data)],
        ["Lớp học phần", countOf(courses.data)],
        ["Lớp hành chính", countOf(classes.data)],
        ["Bài cần xử lý", pending.data?.total],
      ]) {
        const shown = await adminMetric(label);
        check(`so lieu '${label}' khop API`, shown === String(expected), `UI=${shown} API=${expected}`);
      }
      await shot("01-dashboard");

      const routes = [
        ["/admin/courses", "Lớp học phần"],
        ["/admin/classes", "Lớp hành chính"],
        ["/admin/accounts", "Quản lý tài khoản người dùng"],
        ["/admin/submissions", "Quản lý bài nộp"],
        ["/admin/problem-bank", "Ngân hàng đề"],
        ["/admin/settings", "Cấu hình & bảo mật"],
        ["/admin/dashboard", "Tổng quan quản trị"],
      ];
      for (const [href, title] of routes) {
        await page.locator(`a[href="${href}"]`).first().click();
        await page.waitForURL(`**${href}`, { timeout: 25_000 });
        await page.getByRole("heading", { level: 1, name: title }).waitFor({ timeout: 25_000 }).catch(() => {});
        const shown = await heading().catch(() => "");
        check(`sidebar -> ${href}`, shown.includes(title), shown);
      }
    });

    // ── 3. Quản lý tài khoản ──────────────────────────────────────────
    await section("Tai khoan", async () => {
      await open("/admin/accounts");
      await page.locator("tbody tr").first().waitFor({ timeout: 20_000 });
      const statCard = (label) => page.locator("div.rounded-2xl").filter({ hasText: label }).first();
      for (const [label, query] of [
        ["Tổng số tài khoản", ""],
        ["Sinh viên (Role 3)", "&role_id=3"],
        ["Giảng viên (Role 2)", "&role_id=2"],
      ]) {
        const expected = (await api("GET", `/users?page=1&page_size=1${query}`, { token: adminToken })).data?.total;
        const shown = await metric(statCard(label));
        check(`the '${label}' khop API`, shown === String(expected), `UI=${shown} API=${expected}`);
      }
      await shot("02-accounts");

      // Lọc theo vai trò: mọi dòng phải đúng vai trò.
      await page.getByLabel("Lọc tài khoản theo vai trò").selectOption("teacher");
      await page.waitForTimeout(1200);
      const teacherRows = await page.locator("tbody tr").allInnerTexts();
      check("loc Giang vien chi con giang vien",
        teacherRows.length > 0 && teacherRows.every((row) => row.includes("Giảng viên")), `${teacherRows.length} dong`);
      await page.getByLabel("Lọc tài khoản theo vai trò").selectOption("student");
      await page.waitForTimeout(1200);
      const studentRows = await page.locator("tbody tr").allInnerTexts();
      check("loc Sinh vien chi con sinh vien",
        studentRows.length > 0 && studentRows.every((row) => row.includes("Sinh viên")), `${studentRows.length} dong`);
      const mssvShown = (await page.locator("tbody tr").first().locator("td").nth(5).innerText()).trim();
      check("cot MSSV cua tai khoan la 10 chu so", MSSV_PATTERN.test(mssvShown), mssvShown);

      // Tìm kiếm trong trang hiện tại.
      const search = page.getByLabel("Tìm tài khoản trong trang hiện tại");
      await search.fill(mssvShown);
      await page.waitForTimeout(400);
      check("tim theo MSSV ra dung 1 dong", (await page.locator("tbody tr").count()) === 1);
      await search.fill(`khong-co-${stamp}`);
      await page.waitForTimeout(400);
      check("tim khong thay -> thong bao rong", (await body()).includes("Không có tài khoản khớp trong trang này."));
      await search.fill("");
      await page.getByLabel("Lọc tài khoản theo vai trò").selectOption("all");
      await page.waitForTimeout(800);

      // Form cấp tài khoản: dữ liệu sai không được gọi API.
      await page.getByRole("button", { name: "Cấp tài khoản" }).click();
      const modal = dialog();
      const submitAccount = modal.getByRole("button", { name: "Cấp phát tài khoản" });
      await page.fill("#account-student-code", "123");
      await page.fill("#account-name", NEW_STUDENT_NAME);
      await page.fill("#account-email", NEW_STUDENT_EMAIL);
      await page.fill("#account-class", SEED_CLASS_ID);
      check("MSSV 3 chu so -> khong goi API", (await writesDuring(() => submitAccount.click())) === 0);

      await page.fill("#account-student-code", NEW_STUDENT_CODE);
      await page.fill("#account-email", "sai-duoi@gmail.com");
      check("email sai duoi -> khong goi API", (await writesDuring(() => submitAccount.click())) === 0);
      check("email sai duoi -> hien loi ro rang",
        (await modal.locator("#account-email-error").innerText().catch(() => "")).includes("@st.utc2.edu.vn"));

      // Tạo sinh viên mới.
      await page.fill("#account-email", NEW_STUDENT_EMAIL);
      const studentStatus = await submitAndStatus(/\/students$/, "POST", () => submitAccount.click());
      check("tao sinh vien -> 201", studentStatus === 201, String(studentStatus));
      await modal.locator("code").waitFor({ timeout: 10_000 });
      const studentTemp = (await modal.locator("code").innerText()).trim();
      check("mat khau tam sinh vien = MSSV", studentTemp === NEW_STUDENT_CODE, studentTemp);
      await shot("03-account-created");
      await modal.getByRole("button", { name: "Đóng", exact: true }).last().click();
      created.student = studentStatus === 201;

      const studentLogin = await apiLogin(NEW_STUDENT_EMAIL, NEW_STUDENT_CODE);
      check("sinh vien moi dang nhap duoc bang mat khau tam", studentLogin.status === 200, String(studentLogin.status));
      // /users/me không trả field này; cờ chỉ có trong response đăng nhập.
      check("sinh vien moi bi buoc doi mat khau", studentLogin.user?.must_change_password === true);

      // Trùng MSSV -> báo lỗi, không tạo thêm.
      await page.getByRole("button", { name: "Cấp tài khoản" }).click();
      await page.fill("#account-student-code", NEW_STUDENT_CODE);
      await page.fill("#account-name", NEW_STUDENT_NAME);
      await page.fill("#account-email", `trung${NEW_STUDENT_EMAIL}`);
      await page.fill("#account-class", SEED_CLASS_ID);
      const duplicate = await submitAndStatus(/\/students$/, "POST", () => dialog().getByRole("button", { name: "Cấp phát tài khoản" }).click());
      check("trung MSSV -> bi tu choi", duplicate !== null && duplicate >= 400 && duplicate < 500, String(duplicate));
      check("trung MSSV -> co thong bao loi", (await page.locator('[data-sonner-toast][data-type="error"]').count()) > 0);

      // Tạo giảng viên trong cùng cửa sổ.
      await dialog().getByRole("button", { name: "Giảng viên", exact: true }).click();
      check("tab Giang vien an o MSSV", (await page.locator("#account-student-code").count()) === 0);
      await page.fill("#account-name", NEW_TEACHER_NAME);
      await page.fill("#account-email", NEW_TEACHER_EMAIL);
      const teacherStatus = await submitAndStatus(/\/teachers$/, "POST", () => dialog().getByRole("button", { name: "Cấp phát tài khoản" }).click());
      check("tao giang vien -> 201", teacherStatus === 201, String(teacherStatus));
      await dialog().locator("code").waitFor({ timeout: 10_000 });
      const teacherTemp = (await dialog().locator("code").innerText()).trim();
      check("mat khau tam giang vien = email", teacherTemp === NEW_TEACHER_EMAIL, teacherTemp);
      await dialog().getByRole("button", { name: "Đóng", exact: true }).last().click();
      created.teacher = teacherStatus === 201;
      const teacherLogin = await apiLogin(NEW_TEACHER_EMAIL, NEW_TEACHER_EMAIL);
      check("giang vien moi dang nhap duoc", teacherLogin.status === 200, String(teacherLogin.status));

      // Đặt lại mật khẩu: chỉ làm trên sinh viên vừa tạo, không đụng tài khoản seed.
      const row = await findAccountRow(NEW_STUDENT_EMAIL, "student");
      check("sinh vien moi co trong danh sach", row !== null, NEW_STUDENT_EMAIL);
      if (row) {
        await row.getByRole("button", { name: "Đặt lại MK" }).click();
        check("cua so dat lai MK hien dung tai khoan", (await dialog().innerText()).includes(NEW_STUDENT_EMAIL));
        const resetStatus = await submitAndStatus(/\/reset-password$/, "POST", () => dialog().getByRole("button", { name: "Xác nhận đặt lại" }).click());
        check("dat lai MK thanh cong", resetStatus !== null && resetStatus < 300, String(resetStatus));
        await dialog().locator("code").waitFor({ timeout: 10_000 });
        const resetTemp = (await dialog().locator("code").innerText()).trim();
        await dialog().getByRole("button", { name: "Đóng", exact: true }).last().click();
        check("token cu bi thu hoi sau khi dat lai MK",
          (await api("GET", "/users/me", { token: studentLogin.token })).status === 401);
        check("dang nhap duoc bang mat khau tam moi", (await apiLogin(NEW_STUDENT_EMAIL, resetTemp)).status === 200);
      }

      // Trang nhập Excel: chỉ kiểm tra màn hình và chặn file sai định dạng.
      await open("/admin/accounts/import");
      check("trang nhap Excel co tieu de", (await heading()).includes("Nhập danh sách Sinh viên từ Excel"), await heading());
      await page.locator('input[type="file"]').setInputFiles({
        name: "khong-phai-excel.txt", mimeType: "text/plain", buffer: Buffer.from("abc"),
      });
      check("nhap file .txt -> bao loi dinh dang", await toast("định dạng .xls hoặc .xlsx"));
      await shot("04-accounts-import");
    });

    // ── 4. Lớp hành chính ─────────────────────────────────────────────
    await section("Lop hanh chinh", async () => {
      await open("/admin/classes");
      await page.locator("tbody tr").first().waitFor({ timeout: 20_000 });
      const classes = (await api("GET", "/classes", { token: adminToken })).data ?? [];
      const shownClasses = await adminMetric("Lớp hành chính");
      check("so lop hanh chinh khop API", shownClasses === String(classes.length), `UI=${shownClasses} API=${classes.length}`);

      // Lớp đang có sinh viên thì không được xoá.
      const seedRow = page.locator("tbody tr").filter({ hasText: SEED_CLASS_ID }).first();
      check("lop co sinh vien: nut Xoa bi khoa", await seedRow.getByRole("button", { name: "Xóa lớp" }).isDisabled(), SEED_CLASS_ID);

      // HỒI QUY: cột "MSSV" phải là MSSV, không phải UUID.
      await seedRow.getByRole("button", { name: "Xem sinh viên" }).click();
      await dialog().locator("tbody tr").first().waitFor({ timeout: 15_000 });
      const rosterMssv = (await dialog().locator("tbody tr").first().locator("td").first().innerText()).trim();
      check("danh sach lop: cot MSSV hien MSSV 10 so", MSSV_PATTERN.test(rosterMssv), rosterMssv);
      await shot("05-class-roster");
      await page.keyboard.press("Escape");
      await dialog().waitFor({ state: "hidden", timeout: 5000 }).catch(() => {});

      // Tạo rồi xoá một lớp trống để không để lại dữ liệu.
      await page.getByRole("button", { name: "Tạo lớp hành chính" }).click();
      await dialog().getByLabel("Hệ đào tạo").fill("TEST");
      await dialog().getByLabel("Khóa").fill(NEW_CLASS_NUMBER);
      await dialog().getByLabel("Ngành").fill(NEW_CLASS_DEPARTMENT);
      const newClassId = (await dialog().locator("strong").first().innerText()).trim();
      check("xem truoc ma lop dung dinh dang", newClassId === `TEST.${NEW_CLASS_NUMBER}.${NEW_CLASS_DEPARTMENT}`, newClassId);
      const createStatus = await submitAndStatus(/\/classes$/, "POST", () => dialog().getByRole("button", { name: "Tạo lớp", exact: true }).click());
      check("tao lop hanh chinh -> 201", createStatus === 201, String(createStatus));
      check("tao lop -> co toast", await toast("Đã tạo lớp hành chính."));

      await page.getByLabel("Tìm lớp hành chính").fill(NEW_CLASS_DEPARTMENT);
      const newRow = page.locator("tbody tr").filter({ hasText: newClassId }).first();
      const rowVisible = await newRow.waitFor({ timeout: 10_000 }).then(() => true).catch(() => false);
      check("lop moi xuat hien + tim duoc", rowVisible, newClassId);
      if (rowVisible) {
        await newRow.getByRole("button", { name: "Xóa lớp" }).click();
        const deleteStatus = await submitAndStatus(/\/classes\//, "DELETE", () => dialog().getByRole("button", { name: "Xác nhận" }).click());
        check("xoa lop trong -> 204", deleteStatus === 204, String(deleteStatus));
        check("xoa lop -> co toast", await toast("Đã xóa lớp hành chính."));
        const gone = await api("GET", `/classes/${encodeURIComponent(newClassId)}`, { token: adminToken });
        check("lop da xoa khoi he thong", gone.status === 404, String(gone.status));
      }
    });

    // ── 5. Ngân hàng đề: tạo đề nguồn ─────────────────────────────────
    await section("Ngan hang de", async () => {
      await open("/admin/problem-bank");
      await page.locator("article").first().waitFor({ timeout: 20_000 });
      await page.getByLabel("Tìm bài tập nguồn").fill(SEED_PROBLEM_TITLE);
      await page.waitForTimeout(1000);
      check("tim bai seed trong ngan hang", (await page.locator("article").filter({ hasText: SEED_PROBLEM_TITLE }).count()) > 0, SEED_PROBLEM_TITLE);
      await page.getByLabel("Tìm bài tập nguồn").fill("");
      await page.getByLabel("Lọc độ khó").selectOption("hard");
      await page.waitForTimeout(1000);
      const hardCards = await page.locator("article").allInnerTexts();
      check("loc do kho Kho chi con bai Kho", hardCards.every((card) => card.includes("Khó")), `${hardCards.length} bai`);
      await page.getByLabel("Lọc độ khó").selectOption("");
      await page.waitForTimeout(800);

      // Button asChild render <a role="button"> nên không tìm được bằng role "link".
      const firstCard = page.locator("article").first();
      await firstCard.locator("a", { hasText: "Xem chi tiết" }).click();
      await page.waitForURL(/\/admin\/problem-bank\/\d+/, { timeout: 25_000 });
      await page.waitForTimeout(1500);
      check("mo chi tiet bai khong loi", !ERROR_TEXT.test(await body()), page.url());
      await shot("06-bank-detail");

      await open("/admin/problem-bank");
      await page.getByRole("button", { name: "Tạo bài tập nguồn" }).click();
      const form = dialog();
      await form.getByLabel("Tên bài tập").fill(NEW_PROBLEM_TITLE);
      await form.getByLabel("Tên hàm cần chấm").fill("1abc");
      await form.getByLabel("Mở đề (giờ Việt Nam)").fill(dateTimeLocal(-1));
      await form.getByLabel("Hạn nộp (giờ Việt Nam)").fill(dateTimeLocal(30));
      await form.getByLabel("Nội dung đề bài").fill("Viet ham sum_two(a, b) tra ve tong hai so.");
      await form.getByLabel("Ràng buộc").fill("-10^9 <= a, b <= 10^9");
      const submitProblem = form.getByRole("button", { name: "Tạo bài tập nguồn" });

      check("ten ham sai -> khong goi API", (await writesDuring(() => submitProblem.click())) === 0);
      check("ten ham sai -> co thong bao", await toast("tên hàm hợp lệ"));
      await form.getByLabel("Tên hàm cần chấm").fill("sum_two");

      check("thieu ma khoi tao -> khong goi API", (await writesDuring(() => submitProblem.click())) === 0);
      check("thieu ma khoi tao -> co thong bao", await toast("mã nguồn khởi tạo"));
      const starters = {
        python: "def sum_two(a, b):\n    pass\n",
        c: "int sum_two(int a, int b) {\n    return 0;\n}\n",
        cpp: "int sum_two(int a, int b) {\n    return 0;\n}\n",
        java: "class Solution {\n    int sum_two(int a, int b) {\n        return 0;\n    }\n}\n",
      };
      for (const [language, code] of Object.entries(starters)) {
        // Khớp đúng tên: "C" không được trùng "CPP" (nút có thêm " ✓" khi đã nhập mã).
        await form.getByRole("button", { name: new RegExp(`^${language}( ✓)?$`, "i") }).click();
        await form.getByLabel(`Mã khởi tạo ${language}`).fill(code);
      }

      await form.getByLabel("Input JSON").fill("khong-phai-json");
      check("testcase sai JSON -> khong goi API", (await writesDuring(() => submitProblem.click())) === 0);
      check("testcase sai JSON -> co thong bao", await toast("JSON hợp lệ"));
      await form.getByLabel("Input JSON").fill("[1, 2]");
      await form.getByLabel("Output JSON").fill("3");
      await shot("07-bank-create-form");

      const status = await submitAndStatus(/\/problems$/, "POST", () => submitProblem.click());
      check("tao de nguon -> 201", status === 201, String(status));
      check("tao de nguon -> co toast", await toast("Đã tạo bài tập nguồn."));
      created.problem = status === 201;

      await page.getByLabel("Tìm bài tập nguồn").fill(NEW_PROBLEM_TITLE);
      const card = page.locator("article").filter({ hasText: NEW_PROBLEM_TITLE }).first();
      const visible = await card.waitFor({ timeout: 10_000 }).then(() => true).catch(() => false);
      check("de nguon moi xuat hien", visible, NEW_PROBLEM_TITLE);
      if (visible) check("the de nguon ghi 1 testcase + 'De nguon'", /1 testcase · Đề nguồn/.test(await card.innerText()));
    });

    // ── 6. Lớp học phần ───────────────────────────────────────────────
    await section("Lop hoc phan", async () => {
      await open("/admin/courses");
      const courses = (await api("GET", "/courses", { token: adminToken })).data;
      const shown = await adminMetric("Tổng lớp học phần");
      check("tong lop hoc phan khop API", shown === String(countOf(courses)), `UI=${shown} API=${countOf(courses)}`);

      const search = page.getByLabel("Tìm lớp học phần");
      await search.fill(SEED_COURSE_ID);
      await page.waitForTimeout(400);
      check("tim lop seed theo ma", (await page.locator(`a[href="/admin/courses/${SEED_COURSE_ID}"]`).count()) > 0, SEED_COURSE_ID);
      await search.fill(`khong-co-${stamp}`);
      await page.waitForTimeout(400);
      check("tim khong thay -> trang thai rong", (await body()).includes("Không tìm thấy lớp phù hợp"));
      await search.fill("");
      await page.getByRole("button", { name: "Dạng danh sách" }).click();
      check("chuyen dang danh sach", (await page.getByRole("button", { name: "Dạng danh sách" }).getAttribute("aria-pressed")) === "true");
      await page.getByRole("button", { name: "Dạng lưới" }).click();
      await shot("08-courses");

      // Tạo lớp: ngày kết thúc trước ngày bắt đầu không được gọi API.
      await page.getByRole("button", { name: "Tạo lớp học phần" }).click();
      const form = dialog();
      await form.getByLabel("Mã lớp").fill(NEW_COURSE_ID);
      await form.getByLabel("Tên lớp học phần").fill(NEW_COURSE_NAME);
      await form.getByLabel("Học kỳ / năm học").fill("HK1 2026-2027");
      await form.getByLabel("Ngày bắt đầu").fill(dateOnly(10));
      await form.getByLabel("Ngày kết thúc").fill(dateOnly(5));
      const saveCourse = form.getByRole("button", { name: "Lưu lớp học phần" });
      check("ngay ket thuc truoc ngay bat dau -> khong goi API", (await writesDuring(() => saveCourse.click())) === 0);
      await form.getByLabel("Ngày bắt đầu").fill(dateOnly(-1));
      await form.getByLabel("Ngày kết thúc").fill(dateOnly(60));
      const status = await submitAndStatus(/\/courses$/, "POST", () => saveCourse.click());
      check("tao lop hoc phan -> 201", status === 201, String(status));
      check("tao lop -> co toast", await toast("Đã tạo lớp học phần."));
      created.course = status === 201;
      if (!created.course) return;

      // Trang chi tiết.
      const link = page.locator(`a[href="/admin/courses/${NEW_COURSE_ID}"]`).first();
      await link.waitFor({ timeout: 10_000 });
      await link.click();
      await page.waitForURL(`**/admin/courses/${NEW_COURSE_ID}`, { timeout: 25_000 });
      await page.getByRole("heading", { level: 1 }).filter({ hasText: NEW_COURSE_ID }).waitFor({ timeout: 25_000 });
      check("chi tiet lop co ten va ma", (await heading()).includes(NEW_COURSE_NAME), await heading());
      const creator = (await page.getByText("Người tạo:").locator("strong").first().innerText()).trim();
      check("nguoi tao hien ten, khong hien UUID", !UUID_PATTERN.test(creator), creator);

      // Sửa lớp: mã lớp bị khoá, đổi được tên.
      await page.getByRole("button", { name: "Chỉnh sửa lớp" }).click();
      check("sua lop: ma lop bi khoa", await dialog().getByLabel("Mã lớp").isDisabled());
      await dialog().getByLabel("Tên lớp học phần").fill(`${NEW_COURSE_NAME} sua`);
      const patch = await submitAndStatus(new RegExp(`/courses/${NEW_COURSE_ID}$`), "PATCH", () => dialog().getByRole("button", { name: "Lưu lớp học phần" }).click());
      check("sua lop -> 200", patch === 200, String(patch));
      const renamed = await page.getByRole("heading", { level: 1 }).filter({ hasText: `${NEW_COURSE_NAME} sua` })
        .waitFor({ timeout: 10_000 }).then(() => true).catch(() => false);
      check("sua lop -> tieu de cap nhat", renamed);

      // Tạo buổi học.
      await page.getByRole("button", { name: "Tạo buổi học" }).click();
      await dialog().getByLabel("Tên buổi học").fill(NEW_LESSON_NAME);
      const lessonStatus = await submitAndStatus(new RegExp(`/courses/${NEW_COURSE_ID}/lessons$`), "POST", () => dialog().getByRole("button", { name: "Lưu buổi học" }).click());
      check("tao buoi hoc -> 2xx", lessonStatus !== null && lessonStatus < 300, String(lessonStatus));
      const lessonCard = page.locator("article").filter({ hasText: NEW_LESSON_NAME }).first();
      created.lesson = await lessonCard.waitFor({ timeout: 10_000 }).then(() => true).catch(() => false);
      check("buoi hoc moi xuat hien", created.lesson, NEW_LESSON_NAME);

      // Tab sinh viên.
      await page.getByRole("tab", { name: "Sinh viên" }).click();
      await page.getByRole("button", { name: "Thêm sinh viên" }).waitFor({ timeout: 10_000 });
      check("lop moi chua co sinh vien", (await body()).includes("Chưa có sinh viên phù hợp"));

      // HỒI QUY: form ghi "Theo MSSV" nên nhập MSSV phải thêm được sinh viên.
      if (created.student) {
        await page.getByRole("button", { name: "Thêm sinh viên" }).click();
        await dialog().getByLabel("MSSV").fill(NEW_STUDENT_CODE);
        const byCode = await submitAndStatus(/\/enrollments$/, "POST", () => dialog().getByRole("button", { name: "Thêm vào lớp" }).click());
        check("them sinh vien theo MSSV -> thanh cong", byCode !== null && byCode < 300, `MSSV=${NEW_STUDENT_CODE} status=${byCode}`);
        await shot("09-enroll-by-mssv");
        if (await dialog().isVisible().catch(() => false)) {
          await dialog().getByRole("button", { name: "Hủy" }).click();
          await dialog().waitFor({ state: "hidden", timeout: 5000 }).catch(() => {});
        }
      } else {
        skip("them sinh vien theo MSSV", "khong tao duoc sinh vien o buoc truoc");
      }

      // Thêm theo lớp hành chính.
      await page.getByRole("button", { name: "Thêm sinh viên" }).click();
      await dialog().getByRole("button", { name: "Theo lớp hành chính" }).click();
      await dialog().locator("select").selectOption(SEED_CLASS_ID);
      const byClass = await submitAndStatus(/\/enrollments\/class$/, "POST", () => dialog().getByRole("button", { name: "Thêm vào lớp" }).click());
      check("them theo lop hanh chinh -> 2xx", byClass !== null && byClass < 300, String(byClass));
      check("them theo lop -> toast co so luong", await toast(/Đã thêm \d+ sinh viên/));
      await page.locator("tbody tr").first().waitFor({ timeout: 10_000 });
      const enrolled = await page.locator("tbody tr").count();
      check("danh sach sinh viên co du lieu", enrolled > 0, `${enrolled} sinh vien`);

      // HỒI QUY: cột "MSSV" của lớp học phần cũng phải là MSSV.
      const rosterMssv = (await page.locator("tbody tr").first().locator("td").first().innerText()).trim();
      check("lop hoc phan: cot MSSV hien MSSV 10 so", MSSV_PATTERN.test(rosterMssv), rosterMssv);
      await shot("10-course-roster");

      await page.locator("tbody tr").first().getByRole("button", { name: "Xóa khỏi lớp" }).click();
      const removed = await submitAndStatus(/\/enrollments\//, "DELETE", () => dialog().getByRole("button", { name: "Xác nhận" }).click());
      check("xoa sinh vien khoi lop -> 2xx", removed !== null && removed < 300, String(removed));
      check("xoa sinh vien -> co toast", await toast("Đã xóa sinh viên khỏi lớp học phần."));
      await page.waitForTimeout(1000);
      check("so sinh vien giam 1", (await page.locator("tbody tr").count()) === enrolled - 1);

      // Bảng điểm.
      await page.getByRole("tab", { name: "Bảng điểm" }).click();
      await page.waitForTimeout(800);
      check("tab Bang diem khong loi", !ERROR_TEXT.test(await body()));
      await shot("11-course-grades");

      // Trang quản lý buổi học + gắn đề từ ngân hàng.
      await page.getByRole("tab", { name: "Buổi học" }).click();
      if (!created.lesson) return;
      await page.locator("article").filter({ hasText: NEW_LESSON_NAME }).first().locator("a", { hasText: "Quản lý buổi học" }).click();
      await page.waitForURL(/\/sessions\/\d+$/, { timeout: 25_000 });
      await page.getByRole("heading", { level: 1 }).filter({ hasText: NEW_LESSON_NAME }).waitFor({ timeout: 25_000 });
      check("trang buoi hoc co tieu de", (await heading()).includes(NEW_LESSON_NAME), await heading());
      check("buoi moi chua co bai", (await body()).includes("Buổi học chưa có bài tập"));

      if (!created.problem) {
        skip("gan de vao buoi hoc", "khong tao duoc de nguon o buoc truoc");
        return;
      }
      await page.getByRole("button", { name: "Thêm từ ngân hàng đề" }).click();
      await dialog().getByLabel("Tìm bài để gắn vào buổi học").fill(NEW_PROBLEM_TITLE);
      const option = dialog().locator("label").filter({ hasText: NEW_PROBLEM_TITLE }).first();
      await option.waitFor({ timeout: 10_000 });
      await option.locator('input[type="checkbox"]').check();
      const attach = await submitAndStatus(/\/lessons\/\d+\/problems$/, "POST", () => dialog().getByRole("button", { name: /Thêm 1 bài tập/ }).click());
      check("gan de vao buoi hoc -> 2xx", attach !== null && attach < 300, String(attach));
      check("gan de -> co toast", await toast("Đã gắn bài tập vào buổi học."));
      const contentLink = page.locator("a", { hasText: "Nội dung & testcase" }).first();
      const attached = await contentLink.waitFor({ timeout: 10_000 }).then(() => true).catch(() => false);
      check("buoi hoc hien bai vua gan", attached);
      await shot("12-lesson-detail");
      if (attached) {
        await contentLink.click();
        await page.waitForURL(/\/problems\/\d+$/, { timeout: 25_000 });
        await page.getByText(NEW_PROBLEM_TITLE).first().waitFor({ timeout: 25_000 }).catch(() => {});
        const problemText = await body();
        check("trang bai trong buoi co noi dung", problemText.includes(NEW_PROBLEM_TITLE) && !ERROR_TEXT.test(problemText), page.url());
        await shot("13-lesson-problem");
      }
    });

    // ── 7. Xoá đề nguồn sau khi đã gắn vào buổi học ───────────────────
    await section("Xoa de nguon", async () => {
      if (!created.problem) {
        skip("xoa de nguon", "khong tao duoc de nguon");
        return;
      }
      await open("/admin/problem-bank");
      await page.getByLabel("Tìm bài tập nguồn").fill(NEW_PROBLEM_TITLE);
      const source = page.locator("article").filter({ hasText: NEW_PROBLEM_TITLE }).filter({ hasText: "Đề nguồn" }).first();
      await source.waitFor({ timeout: 10_000 });
      page.once("dialog", (confirm) => void confirm.accept());
      const status = await submitAndStatus(/\/problems\/\d+$/, "DELETE", () => source.getByRole("button", { name: "Xóa" }).click());
      check("xoa de nguon -> 2xx", status !== null && status < 300, String(status));
      check("xoa de nguon -> co toast", await toast("Đã xóa đề nguồn."));
      await page.waitForTimeout(1000);
      const left = await page.locator("article").filter({ hasText: NEW_PROBLEM_TITLE }).filter({ hasText: "Đề nguồn" }).count();
      check("de nguon bien mat khoi danh sach", left === 0);
    });

    // ── 8. Bài nộp ────────────────────────────────────────────────────
    await section("Bai nop", async () => {
      await open("/admin/submissions");
      await page.locator("tbody tr").first().waitFor({ timeout: 20_000 });
      const all = (await api("GET", "/submissions/pending?filter=all&limit=500&include_graded=true", { token: adminToken })).data;
      const shownAll = await adminMetric("Tổng bài nộp khớp tìm kiếm");
      check("tong bai nop khop API", shownAll === String(all?.counts?.all), `UI=${shownAll} API=${all?.counts?.all}`);
      await shot("14-submissions");

      await page.getByRole("button", { name: "Đã chấp nhận" }).click();
      await page.waitForTimeout(1200);
      const accepted = await page.locator("tbody tr").allInnerTexts();
      check("loc Da chap nhan chi con bai dat", accepted.length > 0 && accepted.every((row) => row.includes("Đã chấm") || row.includes("Đã chấp nhận")), `${accepted.length} dong`);
      await page.getByRole("button", { name: "Tất cả" }).click();
      await page.waitForTimeout(800);

      await page.getByLabel("Tìm bài nộp").fill(SEED_PROBLEM_TITLE);
      await page.waitForTimeout(1200);
      const matched = await page.locator("tbody tr").allInnerTexts();
      check("tim theo ten bai", matched.length > 0 && matched.every((row) => row.includes(SEED_PROBLEM_TITLE)), `${matched.length} dong`);
      await page.getByLabel("Tìm bài nộp").fill("");
      await page.getByLabel("Lọc lớp học phần").selectOption(SEED_COURSE_ID);
      await page.waitForTimeout(1200);
      check("loc theo lop hoc phan khong loi", !ERROR_TEXT.test(await body()) && (await page.locator("tbody tr").count()) > 0);
      await page.getByLabel("Lọc lớp học phần").selectOption("");
      await page.waitForTimeout(800);

      // Xuất kết quả: downloadCsv cố ý xuất .xls dạng bảng HTML để Excel mở được.
      const [download] = await Promise.all([
        page.waitForEvent("download", { timeout: 15_000 }),
        page.getByRole("button", { name: "Xuất kết quả đang lọc" }).click(),
      ]);
      check("xuat ket qua dung ten file", download.suggestedFilename() === "bai-nop.xls", download.suggestedFilename());
      const exported = readFileSync(await download.path(), "utf8");
      const exportedRows = (exported.match(/<tr>/g) ?? []).length;
      check("file xuat co tieu de + du dong du lieu",
        exported.includes("Mã bài nộp") && exportedRows === all.items.length + 1, `${exportedRows} dong, API ${all.items.length} bai`);

      // Đánh giá bài nộp: sửa rồi khôi phục để không làm bẩn dữ liệu seed.
      const graded = (await api("GET", "/submissions/pending?filter=graded&limit=50&include_graded=true", { token: adminToken })).data?.items ?? [];
      const target = graded[0];
      if (!target) {
        skip("danh gia bai nop", "khong co bai da chap nhan");
        return;
      }
      const original = (await api("GET", `/submissions/${target.id}`, { token: adminToken })).data;
      try {
        await open(`/admin/submissions/${target.id}`);
        check("chi tiet bai nop co tieu de", (await heading()).includes(`#${target.id}`), await heading());
        check("chi tiet co ma nguon", (await page.locator("pre code").innerText()).trim().length > 0);
        const scoreInput = page.getByLabel("Điểm chốt (0–10)");
        const save = page.getByRole("button", { name: "Lưu đánh giá" });
        await scoreInput.fill("11");
        check("diem 11 -> khong goi API", (await writesDuring(() => save.click())) === 0);

        const marker = `Nhan xet test ${stamp}`;
        await scoreInput.fill("9.5");
        await page.getByLabel("Nhận xét").fill(marker);
        const saved = await submitAndStatus(new RegExp(`/submissions/${target.id}$`), "PATCH", () => save.click());
        check("luu danh gia -> 200", saved === 200, String(saved));
        check("luu danh gia -> co toast", await toast("Đã lưu đánh giá bài nộp."));
        await open(`/admin/submissions/${target.id}`);
        check("sau tai lai: giu nhan xet", (await page.getByLabel("Nhận xét").inputValue()) === marker);
        check("sau tai lai: giu diem chot", (await page.getByLabel("Điểm chốt (0–10)").inputValue()) === "9.5");
        await shot("15-submission-detail");
      } finally {
        const restored = await api("PATCH", `/submissions/${target.id}`, {
          token: adminToken,
          body: { feedback: original.feedback ?? "", status: original.status, manual_score: original.manual_score },
        });
        const after = (await api("GET", `/submissions/${target.id}`, { token: adminToken })).data;
        check("khoi phuc bai nop seed sau test",
          restored.status === 200 && after.status === original.status && after.manual_score === original.manual_score && after.feedback === original.feedback,
          `#${target.id}`);
      }
    });

    // ── 9. Cấu hình ───────────────────────────────────────────────────
    await section("Cau hinh", async () => {
      await open("/admin/settings");
      await page.getByText(ADMIN_EMAIL).first().waitFor({ timeout: 15_000 });
      check("hien email admin", (await body()).includes(ADMIN_EMAIL));
      check("hien vai tro Quan tri vien", (await body()).includes("Quản trị viên"));

      const theme = page.getByLabel("Chế độ hiển thị");
      const initialTheme = await theme.inputValue();
      await theme.selectOption("dark");
      await page.waitForTimeout(500);
      check("doi che do toi", await page.evaluate(() => document.documentElement.classList.contains("dark")));
      await shot("16-settings-dark");
      await theme.selectOption(initialTheme);

      const judgeSection = page.locator("section").filter({ hasText: "Kiểm tra máy chấm Judge0" });
      const run = await submitAndStatus(/\/judge0\/run$/, "POST", () => judgeSection.getByRole("button", { name: "Chạy thử" }).click(), 90_000);
      check("Judge0: chay thu -> 200", run === 200, String(run));
      const judgeResult = await judgeSection.getByText("Hello UTC2", { exact: false }).nth(1).waitFor({ timeout: 15_000 }).then(() => true).catch(() => false);
      check("Judge0: stdout dung", judgeResult);
      const connect = await submitAndStatus(/\/judge0\/test$/, "POST", () => judgeSection.getByRole("button", { name: "Kiểm tra kết nối" }).click(), 90_000);
      check("Judge0: kiem tra ket noi -> 200", connect === 200, String(connect));
      check("Judge0: co toast thanh cong", await toast("Đã nhận phản hồi từ Judge0."));

      const aiSection = page.locator("section").filter({ hasText: "Kiểm tra kết nối AI review" });
      await aiSection.getByRole("button", { name: "Kiểm tra kết nối" }).click();
      const aiStatus = aiSection.getByRole("status");
      const aiOk = await aiStatus.waitFor({ timeout: 30_000 }).then(() => true).catch(() => false);
      const aiText = aiOk ? await aiStatus.innerText() : "";
      check("AI: ket noi thanh cong", aiText.includes("Kết nối AI thành công"), aiText);
      await shot("17-settings");

      // Chỉ kiểm tra chặn mật khẩu yếu: đổi thật sẽ làm tài khoản test sai mật khẩu.
      await page.getByRole("button", { name: "Đổi mật khẩu" }).click();
      const inputs = dialog().locator('input[type="password"]');
      await inputs.nth(0).fill(ADMIN_PASSWORD);
      await inputs.nth(1).fill("Ab1!");
      await inputs.nth(2).fill("Ab1!");
      const weak = await writesDuring(() => dialog().getByRole("button", { name: "Lưu mật khẩu" }).click());
      check("mat khau yeu -> bi chan", weak === 0 && (await page.locator('[data-sonner-toast][data-type="error"]').count()) > 0);
      await dialog().getByRole("button", { name: "Hủy" }).click();
    });

    // ── 10. Đổi ngôn ngữ ──────────────────────────────────────────────
    await section("Ngon ngu", async () => {
      await open("/admin/dashboard");
      const en = page.locator('button:has-text("EN"), [role="radio"]:has-text("EN")').first();
      await en.click();
      await page.waitForTimeout(1000);
      const coursesNav = (await page.locator('a[href="/admin/courses"]').first().innerText()).trim();
      check("EN: sidebar doi ngon ngu", coursesNav === "Courses", coursesNav);
      check("EN: html lang = en", (await page.locator("html").getAttribute("lang")) === "en");
      console.log(`NOTE EN: tieu de trang admin van la "${await heading()}" (cac trang admin chua dung i18n)`);
      await shot("18-dashboard-en");
      await page.locator('button:has-text("VI"), [role="radio"]:has-text("VI")').first().click();
      await page.waitForTimeout(800);
      check("VI: quay lai tieng Viet", (await page.locator("html").getAttribute("lang")) === "vi");
    });

    // ── 11. Màn hình điện thoại ───────────────────────────────────────
    await section("Mobile", async () => {
      await page.setViewportSize({ width: 390, height: 844 });
      for (const path of [
        "/admin/dashboard", "/admin/courses", "/admin/classes", "/admin/accounts",
        "/admin/submissions", "/admin/problem-bank", "/admin/settings",
      ]) {
        await open(path);
        await page.waitForTimeout(800);
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        check(`mobile: ${path} khong tran ngang`, overflow <= 2, `overflow=${overflow}px`);
        await shot(`19-mobile${path.replace(/\//g, "-")}`);
      }
      await page.setViewportSize({ width: 1440, height: 900 });
    });

    // ── 12. Đăng xuất (luôn để cuối) ──────────────────────────────────
    await section("Dang xuat", async () => {
      await open("/admin/dashboard");
      await page.getByRole("button", { name: "Đăng xuất" }).first().click();
      const loggedOut = await page.waitForURL(/\/login/, { timeout: 20_000 }).then(() => true).catch(() => false);
      check("dang xuat -> ve /login", loggedOut, page.url());
      await page.goto(`${FRONTEND}/admin/dashboard`, { waitUntil: "domcontentloaded", timeout: 45_000 });
      const blocked = await page.waitForURL(/\/login/, { timeout: 20_000 }).then(() => true).catch(() => false);
      check("sau dang xuat khong vao lai /admin duoc", blocked, page.url());
    });
  } finally {
    check("khong co loi console/pageerror", consoleErrors.length === 0, consoleErrors.slice(0, 3).join(" | ").slice(0, 400));
    await browser.close();
  }

  console.log("=".repeat(100));
  console.log(`KET QUA: ${passed} PASS, ${failed} FAIL, ${skipped} SKIP  (anh: ${SHOTS})`);
  console.log("=".repeat(100));
  process.exit(failed === 0 ? 0 : 1);
}

main();
