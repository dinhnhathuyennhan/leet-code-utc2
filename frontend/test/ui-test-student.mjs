/**
 * Test GIAO DIEN thật cho luong sinh vien (Playwright + Chromium headless).
 *
 * Chay (tu thu muc frontend/):  npm run test:ui
 * Yeu cau: backend :8000, frontend :3000, judge0 :2358 deu dang chay.
 */

import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// Phải dùng "localhost" (không phải 127.0.0.1): Next.js dev chặn cross-origin
// cho dev resource khi host là IP -> trang render rỗng.
const FRONTEND = process.env.UI_FRONTEND_URL ?? "http://localhost:3000";
const STUDENT_EMAIL = process.env.UI_STUDENT_EMAIL ?? "6251071001@st.utc2.edu.vn";
const STUDENT_PASSWORD = process.env.UI_STUDENT_PASSWORD ?? "Password@123";
/** Mật khẩu mới dùng khi test luồng đổi mật khẩu bắt buộc. */
const NEW_PASSWORD_FALLBACK = process.env.UI_NEW_PASSWORD ?? "UiTest@2026";

const here = dirname(fileURLToPath(import.meta.url));
// frontend/test -> len 2 cap de ve goc repo, noi chua docs/ui-shots (da gitignore)
const SHOTS = join(here, "..", "..", "docs", "ui-shots");
mkdirSync(SHOTS, { recursive: true });

let passed = 0;
let failed = 0;
const consoleErrors = [];

function check(name, condition, detail = "") {
  if (condition) {
    passed += 1;
    console.log(`PASS ${name.padEnd(46)} ${detail}`);
  } else {
    failed += 1;
    console.log(`FAIL ${name.padEnd(46)} ${detail}`);
  }
}

async function shot(page, name) {
  const file = join(SHOTS, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function main() {
  console.log("=".repeat(96));
  console.log(`UI TEST STUDENT  ->  ${FRONTEND}`);
  console.log("=".repeat(96));

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: "vi-VN",
  });
  const page = await context.newPage();

  /** Chờ tới khi bài nộp không còn ở trạng thái đang chấm (hết dòng "Đang chấm bài..."). */
  async function waitGradingDone(timeout = 90000) {
    await page
      .waitForFunction(() => !document.body.innerText.includes("Đang chấm bài, vui lòng chờ"), null, { timeout })
      .catch(() => {});
    await page.waitForTimeout(500);
  }

  /**
   * Mở trang và chờ tới khi app render xong.
   *
   * Không dùng `networkidle`: production build có request nền (React Query
   * refetch, HMR…) nên mạng không bao giờ "idle" -> goto timeout.
   */
  async function open(path) {
    await page.goto(`${FRONTEND}${path}`, { waitUntil: "domcontentloaded", timeout: 45000 });
    // Chờ React render: body phải có nội dung (không rỗng).
    await page
      .waitForFunction(() => document.body && document.body.innerText.trim().length > 0, {
        timeout: 20000,
      })
      .catch(() => {});
    await page.waitForTimeout(1200);
  }

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const text = msg.text();
      if (!text.includes("401") && !text.includes("Failed to load resource")) {
        consoleErrors.push(text);
      }
    }
  });
  page.on("pageerror", (error) => consoleErrors.push(`pageerror: ${error.message}`));

  try {
    // 1. Trang dang nhap
    await open("/login");
    check("mo trang dang nhap", await page.locator("body").isVisible());
    check("co truong email", (await page.locator('input[type="email"]').count()) > 0);
    check("co truong mat khau", (await page.locator('input[type="password"]').count()) > 0);
    check("co nut dang nhap", (await page.locator('button[type="submit"]').count()) > 0);
    await shot(page, "01-login");

    // 2. Dang nhap (thu ca mat khau seed va mat khau da doi lan truoc)
    let loggedIn = false;
    for (const candidate of [STUDENT_PASSWORD, NEW_PASSWORD_FALLBACK]) {
      await page.fill('input[type="email"]', STUDENT_EMAIL);
      await page.fill('input[type="password"]', candidate);
      await page.click('button[type="submit"]');
      try {
        await page.waitForURL(/\/(student|change-password)/, { timeout: 15000 });
        loggedIn = true;
        break;
      } catch {
        await page.waitForTimeout(1500);
      }
    }
    check("dang nhap duoc", loggedIn, page.url());
    if (!loggedIn) throw new Error("Khong dang nhap duoc");

    // 2b. Neu bi xep buoc doi mat khau (user seed co must_change_password=True)
    //     -> can hoan tat luong nay truoc khi test cac trang khac.
    if (page.url().includes("/change-password")) {
      check("yeu cau doi mat khau lan dau", true, page.url());
      const pwFields = page.locator('input[type="password"]');
      check("form doi mat khau co 3 o", (await pwFields.count()) === 3, `${await pwFields.count()}`);

      // Validate: mat khau moi yeu cau >=8 ky tu, co hoa, so, ky tu dac biet.
      await pwFields.nth(0).fill(STUDENT_PASSWORD);
      await pwFields.nth(1).fill("Ab1!");
      await pwFields.nth(2).fill("Ab1!");
      await page.locator('button[type="submit"]').click();
      await page.waitForTimeout(1500);
      const weakText = await page.locator("body").innerText();
      check(
        "validate mat khau yeu (it nhat 8 ky tu)",
        weakText.includes("ít nhất 8 ký tự") || weakText.includes("ít nhất 8"),
        "",
      );
      await shot(page, "02b-change-password-weak");

      // Mat khau moi TRUNG mat khau hien tai -> bao loi.
      await pwFields.nth(0).fill(STUDENT_PASSWORD);
      await pwFields.nth(1).fill(STUDENT_PASSWORD);
      await pwFields.nth(2).fill(STUDENT_PASSWORD);
      await page.locator('button[type="submit"]').click();
      await page.waitForTimeout(1500);
      const sameText = await page.locator("body").innerText();
      check(
        "validate mat khau moi khong trung mat khau cu",
        sameText.includes("không được trùng") || sameText.includes("khác mật khẩu hiện tại"),
        "",
      );
      await shot(page, "02c-change-password-duplicate");

      // Dat mat khau moi hop le.
      const NEW_PASSWORD = process.env.UI_NEW_PASSWORD ?? NEW_PASSWORD_FALLBACK;
      await pwFields.nth(0).fill(STUDENT_PASSWORD);
      await pwFields.nth(1).fill(NEW_PASSWORD);
      await pwFields.nth(2).fill(NEW_PASSWORD);
      await page.locator('button[type="submit"]').click();
      await page.waitForURL(/\/student\//, { timeout: 25000 });
      check("doi mat khau thanh cong -> ve trang chu", page.url().includes("/student/"), page.url());
      await shot(page, "02d-after-change-password");
    } else {
      check("vao thang trang chu (khong yeu cau doi mat khau)", page.url().includes("/student/"), page.url());
    }

    // 3. Dashboard
    await page.waitForTimeout(1500);
    const dashBody = await page.locator("body").innerText();
    check("dashboard co noi dung", dashBody.length > 100, `${dashBody.length} ky tu`);
    check("dashboard khong bao loi", !/Lỗi|Error|500/i.test(dashBody), "");
    await shot(page, "02-dashboard");

    // 3a. KHONG con bo loc "Nam hoc" (da bo theo yeu cau)
    const yearSelects = page.locator('select[aria-label="Năm học"], select[aria-label="Nam hoc"]');
    check("dashboard khong con chon nam hoc", (await yearSelects.count()) === 0,
      `${await yearSelects.count()} con`);

    // 3b. Dropdown "Hoc ky" co label ro rang, khong con "Hoc ky:" roi
    //     base-ui Select render <button role="combobox"> (khong phai <select>).
    const semesterSelect = page.locator('button[role="combobox"][aria-label="Học kỳ"]');
    check("dashboard co dropdown hoc ky", (await semesterSelect.count()) > 0);
    if ((await semesterSelect.count()) > 0) {
      const dashSemText = (await semesterSelect.first().innerText()).trim();
      check("dropdown hoc ky khong co dau ':' thua",
        !dashSemText.includes(":"), dashSemText.replace(/\n/g, " "));
      check("dropdown hoc ky hien thi ro rang",
        dashSemText.includes("học kỳ") || dashSemText.includes("Học kỳ"), dashSemText);

      // Mo dropdown va chon tung option -> danh sach phai doi.
      await semesterSelect.first().click();
      await page.waitForTimeout(500);
      const options = page.locator('[role="option"]');
      const optionCount = await options.count();
      check("dropdown hoc ky co the chon", optionCount > 0, `${optionCount} option`);
      if (optionCount > 1) {
        const before = await page.locator('a[href*="/student/classes/"]').count();
        await options.nth(1).click();
        await page.waitForTimeout(1200);
        const after = await page.locator('a[href*="/student/classes/"]').count();
        check("chon hoc ky loc duoc danh sach", after <= before, `${before} -> ${after}`);
        await shot(page, "02c-dashboard-filtered");
        // Reset ve "Tat ca hoc ky".
        await semesterSelect.first().click();
        await page.waitForTimeout(400);
        await page.locator('[role="option"]').first().click();
        await page.waitForTimeout(1000);
      }
    }

    // 3c. Dashboard va trang lop hoc dung cung kieu card (anh bia + hover)
    const dashCovers = await page.locator('img[src*="background-"]').count();
    check("dashboard card co anh bia theo ngon ngu", dashCovers > 0, `${dashCovers} anh`);

    // 3d. Hover card -> co hieu scale tren anh bia
    //     Phai hover vao THE (a.group) chu khong phai vao <img>: class
    //     `group-hover:scale-105` ap dung khi hover vao phan tu co class `group`.
    //     Tailwind v4 dung property `scale` rieng (khong phai `transform`).
    const coverCard = page.locator('a[href*="/student/classes/"]').first();
    if ((await coverCard.count()) > 0) {
      await coverCard.hover();
      await page.waitForTimeout(900);
      const style = await page
        .locator('img[src*="background-"]')
        .first()
        .evaluate((el) => {
          const cs = getComputedStyle(el);
          return { transform: cs.transform, scale: cs.scale };
        });
      // Tailwind v4 dùng property `scale` riêng biệt; transform vẫn là "none".
      // Chỉ cần MỘT trong hai thay đổi là hiệu ứng đã chạy.
      const scaleChanged = style.scale !== "none" && style.scale !== "1";
      const transformChanged =
        style.transform !== "none" && !style.transform.includes("matrix(1, 0, 0, 1, 0, 0)");
      check("hover card co hieu scale anh bia", scaleChanged || transformChanged,
        `scale=${style.scale} transform=${style.transform}`);
      await shot(page, "02b-dashboard-hover");
    }

    // 3e. CHUYEN NGON NGU VI/EN — toggle phai doi THAT text, khong phai chi doi mau.
    //     Day la test hoi quy cho loi "toggle chi co VI, khong co EN".
    const langToggle = page.locator('button:has-text("EN"), [role="radio"]:has-text("EN")');
    check("co toggle ngon ngu EN", (await langToggle.count()) > 0, `${await langToggle.count()} nut`);
    if ((await langToggle.count()) > 0) {
      const viBefore = await page.locator("body").innerText();

      // Bam EN.
      await langToggle.first().click();
      await page.waitForTimeout(1200);
      const enAfter = await page.locator("body").innerText();

      check("chuyen EN doi noi dung that",
        enAfter !== viBefore && /Overview|Classes|Assignments|History|Semester|Enrolled/i.test(enAfter),
        enAfter.slice(0, 60).replace(/\n/g, " "));
      check("chuyen EN khong con chu tieng Viet o sidebar",
        !/Tổng quan|Lớp học phần|Bài tập|Lịch sử nộp bài/.test(enAfter), "");
      check("html lang doi sang en", (await page.locator("html").getAttribute("lang")) === "en",
        await page.locator("html").getAttribute("lang"));
      await shot(page, "02d-dashboard-en");

      // Bam VI -> phai quay lai tieng Viet.
      const viToggle = page.locator('button:has-text("VI"), [role="radio"]:has-text("VI")');
      await viToggle.first().click();
      await page.waitForTimeout(1200);
      const viAfter = await page.locator("body").innerText();
      check("chuyen VI quay lai tieng Viet",
        /Tổng quan|Lớp học phần|Bài tập/.test(viAfter), viAfter.slice(0, 60).replace(/\n/g, " "));
      check("html lang quay lai vi", (await page.locator("html").getAttribute("lang")) === "vi",
        await page.locator("html").getAttribute("lang"));
    }

    // 4. Danh sach lop hoc
    await open("/student/classes");
    const classesText = await page.locator("body").innerText();
    check("trang lop hoc co noi dung", classesText.length > 100, `${classesText.length} ky tu`);
    check("trang lop hoc khong bao loi", !/Đã xảy ra lỗi|Internal Server Error/i.test(classesText), "");
    const classCards = await page.locator('a[href*="/student/classes/"]').count();
    check("co the card lop hoc", classCards > 0, `${classCards} the`);
    await shot(page, "03-classes");

    // 4a. Trang lop hoc: bo chon "Nam hoc", dropdown hoc ky dep
    const classYearSelect = page.locator('button[aria-label*="Năm học"], button[aria-label*="Nam hoc"]');
    check("trang lop hoc khong con chon nam hoc", (await classYearSelect.count()) === 0,
      `${await classYearSelect.count()} con`);
    const classSemSelect = page.locator('button[role="combobox"][aria-label="Học kỳ"]');
    check("trang lop hoc co dropdown hoc ky", (await classSemSelect.count()) > 0);
    if ((await classSemSelect.count()) > 0) {
      const semText = (await classSemSelect.first().innerText()).trim();
      check("dropdown hoc ky lop khong co dau ':' thua", !semText.includes(":"),
        semText.replace(/\n/g, " "));
    }
    const classCovers = await page.locator('img[src*="background-"]').count();
    check("card lop hoc co anh bia", classCovers > 0, `${classCovers} anh`);

    // 4b. Loc theo hoc ky -> danh sach thay doi
    if ((await classSemSelect.count()) > 0) {
      const beforeCount = await page.locator('a[href*="/student/classes/"]').count();
      await classSemSelect.first().click();
      await page.waitForTimeout(500);
      const options = page.locator('[role="option"]');
      if ((await options.count()) > 1) {
        await options.nth(1).click();
        await page.waitForTimeout(1500);
        const afterCount = await page.locator('a[href*="/student/classes/"]').count();
        check("loc theo hoc ky thay doi danh sach", afterCount <= beforeCount,
          `${beforeCount} -> ${afterCount}`);
        await shot(page, "03b-classes-filtered");
        await classSemSelect.first().click();
        await page.waitForTimeout(400);
        await page.locator('[role="option"]').first().click();
        await page.waitForTimeout(1000);
      }
    }

    // 5. Chi tiet lop hoc
    const firstClassHref = await page
      .locator('a[href*="/student/classes/"]')
      .first()
      .getAttribute("href");
    check("lay duoc link lop hoc", Boolean(firstClassHref), firstClassHref ?? "");

    // 5a. CLICK (client-side navigation) vao lop -> phai render, khong man hinh trang
    await page.locator('a[href*="/student/classes/"]').first().click();
    await page.waitForTimeout(2500);
    const clickedClassText = await page.locator("body").innerText();
    check("click vao lop hoc khong man hinh trang", clickedClassText.length > 200,
      `${clickedClassText.length} ky tu`);
    check("click vao lop hoc khong loi", !/Đã xảy ra lỗi/i.test(clickedClassText), "");
    await shot(page, "04-class-detail");

    // 5b. Mo tab "Thong tin lop" (mac dinh da active) va tim nut "Lam bai".
    //     Panel buoi hoc expand mac dinh buoi dau nen khong can bam them.
    const infoTab = page.locator('button:has-text("Thông tin lớp")').first();
    if ((await infoTab.count()) > 0) {
      await infoTab.click();
      await page.waitForTimeout(900);
    }
    const doButton = page.locator('a:has-text("Làm bài"), a:has-text("Xem bài")').first();
    check("co nut Lam bai / Xem bai trong lop", (await doButton.count()) > 0,
      `${await doButton.count()} nut`);
    await shot(page, "04b-class-detail-session");

    // 5c. CLICK "Lam bai" -> phai ra man hinh code (KHONG man hinh trang)
    //     Đây là hồi quy của lỗi cache React Query: useCourseWithProblem dùng
    //     chung queryKey với useCourse nhưng trả shape khác -> trang render rỗng.
    if ((await doButton.count()) > 0) {
      const doHref = await doButton.getAttribute("href");
      await doButton.click();
      await page.waitForTimeout(3000);
      const doText = await page.locator("body").innerText();
      check("click Lam bai khong man hinh trang", doText.length > 200,
        `${doText.length} ky tu (${doHref})`);
      check("click Lam bai ra man hinh code",
        (await page.locator('textarea[aria-label="Mã nguồn bài nộp"]').count()) > 0);
      check("click Lam bai co nut Nop bai",
        (await page.locator('button:has-text("Nộp bài")').count()) > 0);
      await shot(page, "04c-class-detail-do-bai");
    }

    // 6. Danh sach bai tap
    await open("/student/assignments");
    const assignText = await page.locator("body").innerText();
    check("trang bai tap co noi dung", assignText.length > 100, `${assignText.length} ky tu`);
    check("trang bai tap khong bao loi", !/Đã xảy ra lỗi/i.test(assignText), "");
    const assignRows = await page.locator('a[href*="/assignments/"]').count();
    check("trang bai tap co link", assignRows > 0, `${assignRows} link`);
    await shot(page, "05-assignments");

    // 6a. CLICK bai tap trong tab "Bai tap" (client-side) -> phai ra man hinh code
    const assignLinkFirst = page.locator('a[href*="/assignments/"]').first();
    const assignClickHref = await assignLinkFirst.getAttribute("href");
    await assignLinkFirst.click();
    await page.waitForTimeout(3000);
    const assignClickedText = await page.locator("body").innerText();
    check("click bai tap khong man hinh trang", assignClickedText.length > 200,
      `${assignClickedText.length} ky tu (${assignClickHref})`);
    check("click bai tap ra man hinh code",
      (await page.locator('textarea[aria-label="Mã nguồn bài nộp"]').count()) > 0);
    await shot(page, "05b-assignments-clicked");

    // 7. Chi tiet bai tap + editor
    // 6a đã điều hướng tới trang chi tiết rồi, nên dùng lại href đã lấy được
    // (không tìm link trên trang hiện tại vì trang chi tiết không có link bài khác).
    const assignHref = assignClickHref;
    check("lay duoc link bai tap", Boolean(assignHref), assignHref ?? "");
    await open(assignHref);

    const editor = page.locator('textarea[aria-label="Mã nguồn bài nộp"]');
    check("co o soan code", (await editor.count()) > 0);
    check("co nut nop bai", (await page.locator('button:has-text("Nộp bài")').count()) > 0);

    const detailText = await page.locator("body").innerText();
    check("chi tiet bai tap co de bai", detailText.includes("Đề bài"), "");
    check("chi tiet bai tap co testcase mau", detailText.includes("Testcase mẫu"), "");
    check("chi tiet bai tap co thoi gian chay", detailText.includes("Thời gian chạy"), "");
    check("chi tiet bai tap co so testcase", detailText.includes("Test cases"), "");

    // 7a. CHUYEN NGON NGU tren trang chi tiet bai tap (noi dung tieng Viet ->
    //     tieng Anh). Kiem tra cac nhan chuyen dich da dung.
    const detailEnBtn = page.locator('button:has-text("EN"), [role="radio"]:has-text("EN")');
    if ((await detailEnBtn.count()) > 0) {
      await detailEnBtn.first().click();
      await page.waitForTimeout(1200);
      const detailEnText = await page.locator("body").innerText();
      check("chi tiet bai tap doi sang tieng Anh",
        /Problem statement|Constraints|Sample test cases|Time limit|Submit|Assignment/.test(detailEnText),
        detailEnText.slice(0, 80).replace(/\n/g, " "));
      check("chi tiet bai tap khong con nhan tieng Viet",
        !/Đề bài|Ràng buộc|Testcase mẫu|Thời gian chạy|Nộp bài/.test(detailEnText), "");
      await shot(page, "06b-assignment-detail-en");

      // Quay lai tieng Viet de cac buoc sau chay voi nhan tieng Viet.
      const detailViBtn = page.locator('button:has-text("VI"), [role="radio"]:has-text("VI")');
      await detailViBtn.first().click();
      await page.waitForTimeout(1000);
      const detailViText = await page.locator("body").innerText();
      check("quay lai tieng Viet tren chi tiet bai tap",
        /Đề bài|Testcase mẫu|Nộp bài/.test(detailViText), "");
    }

    const initialCode = await editor.inputValue();
    check("editor da nap ma mau", initialCode.trim().length > 0, `${initialCode.length} ky tu`);
    await shot(page, "06-assignment-detail");

    // 8. Doi ngon ngu
    const cppTab = page.locator('button:has-text("C++")');
    check("co tab C++", (await cppTab.count()) > 0);
    if ((await cppTab.count()) > 0) {
      await cppTab.first().click();
      await page.waitForTimeout(600);
      const cppCode = await editor.inputValue();
      check("doi sang C++ doi ma mau", cppCode.includes("iostream"), cppCode.split("\n")[0]);
      check("doi sang C++ khong con code python", !cppCode.includes("print("), "");
      await shot(page, "07-editor-cpp");
      await page.locator('button:has-text("Python")').first().click();
      await page.waitForTimeout(600);
    }

    // 9. Nop bai SAI
    await editor.fill("print('SAI_ROI')\n");
    await page.locator('button:has-text("Nộp bài")').first().click();
    await page.waitForSelector("text=Kết quả bài nộp", { timeout: 90000 });
    check("nho bai -> hien ket qua cham", true, "");
    // Panel hiện ngay khi bài còn "pending" -> phải chờ Judge0 chấm xong mới đọc verdict.
    await waitGradingDone();

    const resultText = await page.locator("body").innerText();
    check("ket qua co verdict sai", resultText.includes("Sai kết quả"), "");
    check("ket qua co bang testcase", /Test\s*#?\s*1/i.test(resultText), "");
    await shot(page, "08-result-wrong");

    // 10. Nop bai DUNG
    await editor.fill("import sys\nd = sys.stdin.read().split()\nprint(int(d[0]) + int(d[1]))\n");
    await page.locator('button:has-text("Nộp bài")').first().click();
    await page.waitForTimeout(1000);
    await waitGradingDone();
    const acceptedText = await page.locator("body").innerText();
    check("code dung -> trang thai Dat", acceptedText.includes("Đạt"), "");
    await shot(page, "09-result-accepted");

    // 11. Lich su nop bai
    await open("/student/history");
    const historyText = await page.locator("body").innerText();
    check("trang lich su co noi dung", historyText.length > 100, `${historyText.length} ky tu`);
    check("lich su co bai vua nop", historyText.includes("Tổng hai số"), "");
    check("lich su co trang thai Dat", historyText.includes("Đạt"), "");
    check("lich su co trang thai Sai", historyText.includes("Sai kết quả"), "");
    const historyRows = await page.locator("a[href*='/student/submissions/']").count();
    check("lich su co link chi tiet", historyRows > 0, `${historyRows} link`);
    await shot(page, "10-history");

    // 12. Loc trang thai
    const filterAccepted = page.locator('button:has-text("Đạt")').first();
    if ((await filterAccepted.count()) > 0) {
      await filterAccepted.click();
      await page.waitForTimeout(1200);
      const filtered = await page.locator("body").innerText();
      check("loc trang thai Dat khong loi", !/Đã xảy ra lỗi/i.test(filtered), "");
      await shot(page, "11-history-filter");
    }

    // 13. Chi tiet bai nop
    await open("/student/history");
    const detailHref = await page
      .locator("a[href*='/student/submissions/']")
      .first()
      .getAttribute("href");
    check("lay duoc link chi tiet bai nop", Boolean(detailHref), detailHref ?? "");
    if (detailHref) {
      await open(detailHref);
      const subText = await page.locator("body").innerText();
      check("chi tiet bai nop co noi dung", subText.length > 100, `${subText.length} ky tu`);
      check(
        "chi tiet bai nop co ma nguon",
        subText.includes("Mã nguồn") || subText.includes("Mã nguồn đã nộp"),
        "",
      );
      check(
        "chi tiet bai nop co verdict",
        subText.includes("Đạt") || subText.includes("Sai kết quả"),
        "",
      );
      await shot(page, "12-submission-detail");
    }

    // 13a. CHUYEN NGON NGU tren trang lich su + chi tiet bai nop.
    await open("/student/history");
    const historyEnBtn = page.locator('button:has-text("EN"), [role="radio"]:has-text("EN")');
    if ((await historyEnBtn.count()) > 0) {
      await historyEnBtn.first().click();
      await page.waitForTimeout(1200);
      const historyEnText = await page.locator("body").innerText();
      check("lich su doi sang tieng Anh",
        /Submission history|Accepted|Wrong answer|Compile error|Pending|All/.test(historyEnText),
        historyEnText.slice(0, 80).replace(/\n/g, " "));
      check("lich su khong con nhan tieng Viet",
        !/Lịch sử nộp bài|Sai kết quả|Lỗi biên dịch/.test(historyEnText), "");
      await shot(page, "12b-history-en");

      // Quay lai tieng Viet.
      const historyViBtn = page.locator('button:has-text("VI"), [role="radio"]:has-text("VI")');
      await historyViBtn.first().click();
      await page.waitForTimeout(1000);
      const historyViText = await page.locator("body").innerText();
      check("quay lai tieng Viet tren lich su",
        /Lịch sử nộp bài|Sai kết quả/.test(historyViText), "");
    }

    // 14. Responsive mobile
    await page.setViewportSize({ width: 390, height: 844 });
    await open("/student/classes");
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    check("khong tran ngang tren mobile", overflow <= 2, `overflow=${overflow}px`);
    await shot(page, "13-mobile-classes");

    await open("/student/history");
    const overflow2 = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    check("lich su khong tran ngang tren mobile", overflow2 <= 2, `overflow=${overflow2}px`);
    await shot(page, "14-mobile-history");

    // 15. Loi console
    check("khong co loi runtime trong console", consoleErrors.length === 0,
      consoleErrors.slice(0, 3).join(" | "));
  } catch (error) {
    failed += 1;
    console.log(`FAIL exception: ${error.message}`);
    await shot(page, "99-error");
  } finally {
    await browser.close();
  }

  console.log("=".repeat(96));
  console.log(`RESULT: ${passed} passed, ${failed} failed`);
  console.log(`Screenshots: ${SHOTS}`);
  console.log("=".repeat(96));
  process.exit(failed ? 1 : 0);
}

main();
