/**
 * Test GIAO DIỆN thật cho tính năng "Review code" bằng AI (Playwright + Chromium).
 *
 * Chạy (từ thư mục frontend/):  npm run test:ui-ai-review
 * Yêu cầu: backend :8000, frontend :3000, Judge0 :2358 và Ollama đều đang chạy.
 *
 * Kịch bản:
 *  1. Bài nộp sai / lỗi biên dịch -> KHÔNG có nút Review code.
 *  2. Nộp bài đúng -> có nút; chưa bấm thì KHÔNG gọi AI; bấm -> gọi đúng 1 lần,
 *     request không mang code; hiện loading rồi kết quả thật từ AI.
 *  3. Nộp lại bài sai -> kết quả review cũ và nút biến mất.
 *  4. Trang chi tiết bài nộp: đúng thì có nút, sai thì không; review thật; Đóng.
 *  5. Lỗi giả lập (503 AI_BUSY) -> thẻ lỗi + Thử lại -> thành công.
 *  6. Tiếng Anh, dark mode, màn hình điện thoại.
 *  7. Gọi API trực tiếp: bài sai -> 409, bài người khác -> 404, không token -> 401.
 */

import { chromium, request as playwrightRequest } from "playwright";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const FRONTEND = process.env.UI_FRONTEND_URL ?? "http://localhost:3000";
const API = process.env.UI_API_URL ?? "http://localhost:8000";
const STUDENT_EMAIL = process.env.UI_STUDENT_EMAIL ?? "6751071001@st.utc2.edu.vn";
const OTHER_STUDENT_EMAIL = process.env.UI_OTHER_STUDENT_EMAIL ?? "6751071003@st.utc2.edu.vn";
const PASSWORDS = [process.env.UI_STUDENT_PASSWORD ?? "Password@123", "UiTest@2026"];
const COURSE_ID = process.env.UI_COURSE_ID ?? "DEMO101-2026A";
const PROBLEM_ID = process.env.UI_PROBLEM_ID ?? "47";
const AI_TIMEOUT_MS = 200_000;

const CORRECT_CODE = "import sys\nd = sys.stdin.read().split()\nprint(int(d[0]) + int(d[1]))\n";
const WRONG_CODE = "print('SAI_ROI')\n";

const here = dirname(fileURLToPath(import.meta.url));
const SHOTS = join(here, "..", "..", "docs", "ui-shots", "ai-review");
mkdirSync(SHOTS, { recursive: true });

let passed = 0;
let failed = 0;
const consoleErrors = [];

function check(name, condition, detail = "") {
  if (condition) passed += 1;
  else failed += 1;
  console.log(`${condition ? "PASS" : "FAIL"} ${name.padEnd(64)} ${detail}`);
}

async function shot(page, name) {
  await page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true });
}

/** Đăng nhập API để lấy access token (dùng cho các kiểm tra gọi API trực tiếp). */
async function apiLogin(request, email) {
  for (const password of PASSWORDS) {
    const response = await request.post(`${API}/auth/login`, { data: { email, password } });
    if (response.ok()) return { token: (await response.json()).access_token, password };
  }
  return { token: null, password: null };
}

async function main() {
  console.log("=".repeat(100));
  console.log(`UI TEST AI REVIEW  ->  ${FRONTEND}`);
  console.log("=".repeat(100));

  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "vi-VN" });
  const page = await context.newPage();
  // Context gọi API riêng, KHÔNG dùng chung cookie với trình duyệt: nếu dùng
  // chung, refresh cookie từ login API sẽ xoay vòng/thu hồi phiên của trình duyệt.
  const api = await playwrightRequest.newContext();

  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    // 4xx do test cố ý gây ra (409/404/503 giả lập) không tính là lỗi của trang.
    if (!text.includes("Failed to load resource") && !text.includes("401")) consoleErrors.push(text);
  });
  page.on("pageerror", (error) => consoleErrors.push(`pageerror: ${error.message}`));

  /** Ghi lại mọi request gọi AI review của trang. */
  const aiRequests = [];
  page.on("request", (request) => {
    if (request.url().includes("/ai-review")) {
      aiRequests.push({ url: request.url(), method: request.method(), body: request.postData() });
    }
  });

  async function open(path) {
    await page.goto(`${FRONTEND}${path}`, { waitUntil: "domcontentloaded", timeout: 45_000 });
    await page.waitForFunction(() => document.body.innerText.trim().length > 0, null, { timeout: 20_000 }).catch(() => {});
    await page.waitForTimeout(1200);
  }

  const reviewButton = () => page.getByRole("button", { name: "Review code" });
  const resultCard = () => page.getByTestId("ai-review-result");

  try {
    // ── 0. Đăng nhập ───────────────────────────────────────────────────
    const { token, password } = await apiLogin(api, STUDENT_EMAIL);
    check("API: dang nhap sinh vien", Boolean(token), STUDENT_EMAIL);
    if (!token) throw new Error("Không đăng nhập được sinh viên");

    // Login API ở trên dùng chung cookie jar với trình duyệt -> refresh cookie đã
    // có sẵn, /login có thể tự chuyển sang /student.
    await open("/login");
    // Chờ hoặc form đăng nhập hiện ra, hoặc đã tự chuyển trang.
    await Promise.race([
      page.locator('input[type="email"]').waitFor({ timeout: 30_000 }),
      page.waitForURL(/\/student/, { timeout: 30_000 }),
    ]).catch(() => {});
    console.log(`     (sau khi mo /login: ${page.url()})`);
    if (!page.url().includes("/student")) {
      await page.fill('input[type="email"]', STUDENT_EMAIL);
      await page.fill('input[type="password"]', password);
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/student/, { timeout: 20_000 });
    }
    check("UI: dang nhap", page.url().includes("/student"), page.url());

    // ── 1. Trang làm bài: nộp sai -> không có nút ──────────────────────
    await open(`/student/classes/${encodeURIComponent(COURSE_ID)}/assignments/${PROBLEM_ID}`);
    const editor = page.locator('textarea[aria-label="Mã nguồn bài nộp"]');
    check("trang lam bai co editor", (await editor.count()) > 0);
    check("chua nop bai thi chua co nut Review code", (await reviewButton().count()) === 0);

    const submitButton = page.locator('button:has-text("Nộp bài")').first();
    /**
     * Nộp bài và chờ tới khi CHÍNH bài nộp này chấm xong (theo poll
     * /submissions/{id}/result), tránh khớp nhầm kết quả của lần nộp trước
     * vẫn còn trên màn hình.
     */
    async function submit(code) {
      await editor.fill(code);
      const [submitResponse] = await Promise.all([
        page.waitForResponse((r) => r.request().method() === "POST" && /\/problems\/\d+\/submissions$/.test(r.url()), { timeout: 20_000 }),
        submitButton.click(),
      ]);
      const { submission_id: id } = await submitResponse.json();
      await page.waitForResponse(
        async (r) => {
          if (!r.url().endsWith(`/submissions/${id}/result`)) return false;
          const body = await r.json().catch(() => ({}));
          return body.status && !["pending", "processing"].includes(body.status);
        },
        { timeout: 90_000 },
      );
      await page.waitForTimeout(800);
      return id;
    }

    await submit(WRONG_CODE);
    const wrongText = await page.locator("body").innerText();
    check("nop sai: hien ket qua Sai ket qua", wrongText.includes("Sai kết quả"));
    check("nop sai: KHONG co nut Review code", (await reviewButton().count()) === 0);
    check("nop sai: KHONG co loi moi review", !wrongText.includes("Xem AI nhận xét"));
    await shot(page, "01-wrong-answer-no-button");

    // ── 2. Nộp đúng -> có nút, chỉ gọi AI khi bấm ──────────────────────
    await submit(CORRECT_CODE);
    await page.getByText("10.0", { exact: true }).first().waitFor({ timeout: 10_000 }).catch(() => {});
    check("nop dung: hien 10.0/10", (await page.locator("body").innerText()).includes("10.0"));
    await reviewButton().waitFor({ timeout: 10_000 }).catch(() => {});
    check("nop dung: CO nut Review code", (await reviewButton().count()) === 1);
    check("nop dung: co loi moi 'Bai da pass toan bo testcase'",
      (await page.getByText("Bài đã pass toàn bộ testcase").count()) === 1);
    await page.waitForTimeout(1500);
    check("chua bam: KHONG goi AI", aiRequests.length === 0, `requests=${aiRequests.length}`);
    await shot(page, "02-accepted-has-button");

    const started = Date.now();
    await reviewButton().click();
    const running = page.getByRole("button", { name: /Đang review/ });
    check("dang chay: nut doi thanh 'Dang review…' va bi disable",
      (await running.count()) === 1 && (await running.isDisabled()));
    check("dang chay: hien skeleton", await page.getByTestId("ai-review-loading").isVisible());
    await shot(page, "03-loading");
    // Bấm thêm khi đang chạy (force vì nút đang disable) -> không gửi thêm request.
    await running.click({ force: true }).catch(() => {});

    await resultCard().waitFor({ timeout: AI_TIMEOUT_MS });
    const seconds = ((Date.now() - started) / 1000).toFixed(1);
    check("bam: goi AI dung 1 lan", aiRequests.length === 1, `requests=${aiRequests.length}`);
    const firstRequest = aiRequests[0];
    check("request: POST /submissions/{id}/ai-review",
      firstRequest?.method === "POST" && /\/submissions\/\d+\/ai-review$/.test(firstRequest.url), firstRequest?.url);
    check("request: KHONG gui code len server", !firstRequest?.body || !firstRequest.body.includes("sys.stdin"));
    check("ket qua AI hien thi", await resultCard().isVisible(), `${seconds}s`);

    const cardText = await resultCard().innerText();
    check("ket qua: co the Thoi gian va Bo nho",
      (await page.getByTestId("ai-review-time").count()) === 1 && (await page.getByTestId("ai-review-space").count()) === 1);
    check("ket qua: do phuc tap dang Big O", /O\(/.test(cardText));
    check("ket qua: co muc Diem chua toi uu", cardText.includes("Điểm chưa tối ưu"));
    check("ket qua: co Huong cai thien hoac Da toi uu",
      cardText.includes("Hướng cải thiện") || cardText.includes("Code đã ở mức tối ưu hợp lý"));
    check("ket qua: co chu thich khong anh huong diem", cardText.includes("Không ảnh hưởng tới điểm"));
    check("ket qua: AI tra loi tieng Viet", /[ăâđêôơưạảấầẩậắằẳặẹẻẽếềểệỉịọỏốồổộớờởợụủứừửựỳỷỹ]/i.test(cardText));
    check("ket qua: AI khong chen code block", !cardText.includes("```") && !cardText.includes("def "));
    check("ket qua: nut Review code an di", (await reviewButton().count()) === 0);
    await resultCard().scrollIntoViewIfNeeded();
    await shot(page, "04-result");
    console.log("\n--- Nội dung AI review (trang làm bài) ---\n" + cardText + "\n------------------------------------------\n");

    // ── 3. Nộp lại bài sai -> review cũ biến mất ───────────────────────
    await submit(WRONG_CODE);
    check("nop lai sai: review cu bien mat", (await resultCard().count()) === 0);
    check("nop lai sai: khong co nut Review code", (await reviewButton().count()) === 0);

    // ── 4. Trang chi tiết bài nộp ──────────────────────────────────────
    const acceptedId = Number(firstRequest.url.match(/submissions\/(\d+)\/ai-review/)[1]);
    const mine = await (await api.get(`${API}/submissions/mine?problem_id=${PROBLEM_ID}`, {
      headers: { Authorization: `Bearer ${token}` },
    })).json();
    const wrongSubmission = mine.items.find((item) => item.status === "wrong_answer");

    await open(`/student/submissions/${wrongSubmission.id}`);
    check("chi tiet bai sai: KHONG co nut Review code", (await reviewButton().count()) === 0, `#${wrongSubmission.id}`);
    await shot(page, "05-detail-wrong-no-button");

    aiRequests.length = 0;
    await open(`/student/submissions/${acceptedId}`);
    check("chi tiet bai dung: CO nut Review code", (await reviewButton().count()) === 1, `#${acceptedId}`);
    check("chi tiet bai dung: mo trang KHONG goi AI", aiRequests.length === 0);
    await reviewButton().click();
    await resultCard().waitFor({ timeout: AI_TIMEOUT_MS });
    check("chi tiet bai dung: review thanh cong", await resultCard().isVisible());
    check("chi tiet bai dung: goi dung bai nop",
      aiRequests.length === 1 && aiRequests[0].url.endsWith(`/submissions/${acceptedId}/ai-review`));
    await shot(page, "06-detail-result");

    await page.getByRole("button", { name: "Đóng AI review" }).click();
    await reviewButton().waitFor({ timeout: 5_000 }).catch(() => {});
    check("Dong: an ket qua, hien lai nut", (await resultCard().count()) === 0 && (await reviewButton().count()) === 1);

    // ── 5. Lỗi giả lập -> thẻ lỗi + Thử lại ─────────────────────────────
    let failOnce = true;
    await page.route("**/ai-review", async (route) => {
      if (failOnce) {
        failOnce = false;
        await route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({ error_code: "AI_BUSY", message: "AI đang phân tích bài khác, vui lòng thử lại sau" }),
        });
      } else {
        await route.continue();
      }
    });
    await reviewButton().click();
    // Scope trong section AI: Next.js có sẵn route announcer cũng là role="alert".
    const section = page.getByTestId("ai-review-section");
    const alert = section.getByRole("alert");
    await alert.waitFor({ timeout: 10_000 });
    const alertText = await alert.innerText();
    check("loi AI_BUSY: hien thong bao dung", alertText.includes("AI đang phân tích bài khác"));
    check("loi AI_BUSY: co nut Thu lai", (await alert.getByRole("button", { name: /Thử lại/ }).count()) === 1);
    await shot(page, "07-error-busy");
    await alert.getByRole("button", { name: /Thử lại/ }).click();
    await resultCard().waitFor({ timeout: AI_TIMEOUT_MS });
    check("Thu lai: thanh cong, the loi bien mat", (await section.getByRole("alert").count()) === 0);
    await page.unroute("**/ai-review");

    // ── 6a. Tiếng Anh ──────────────────────────────────────────────────
    await page.evaluate(() => window.localStorage.setItem("utc2:locale", "en"));
    await open(`/student/submissions/${acceptedId}`);
    check("EN: nut Review code + loi moi tieng Anh",
      (await reviewButton().count()) === 1 && (await page.getByText("All testcases passed").count()) === 1);
    await reviewButton().click();
    await resultCard().waitFor({ timeout: AI_TIMEOUT_MS });
    // textContent (không phải innerText) vì nhãn dùng CSS uppercase.
    const enText = await resultCard().evaluate((el) => el.textContent ?? "");
    check("EN: nhan panel tieng Anh",
      ["Time", "Space", "Summary", "Inefficiencies", "Does not affect your grade", "Review again"].every((label) => enText.includes(label)));
    check("EN: khong con nhan tieng Viet cua panel", !enText.includes("Điểm chưa tối ưu"));
    await shot(page, "08-english");
    await page.evaluate(() => window.localStorage.setItem("utc2:locale", "vi"));

    // ── 6b. Dark mode ──────────────────────────────────────────────────
    await page.evaluate(() => window.localStorage.setItem("utc2-local-theme", "dark"));
    await open(`/student/submissions/${acceptedId}`);
    await reviewButton().click();
    await resultCard().waitFor({ timeout: AI_TIMEOUT_MS });
    const isDark = await page.evaluate(() => document.documentElement.classList.contains("dark"));
    const cardBg = await resultCard().evaluate((el) => getComputedStyle(el).backgroundColor);
    check("dark mode: panel dung nen toi", isDark && cardBg !== "rgb(255, 255, 255)", cardBg);
    await resultCard().scrollIntoViewIfNeeded();
    await shot(page, "09-dark");
    await page.evaluate(() => window.localStorage.setItem("utc2-local-theme", "light"));

    // ── 6c. Điện thoại ─────────────────────────────────────────────────
    await page.setViewportSize({ width: 390, height: 844 });
    await open(`/student/submissions/${acceptedId}`);
    await reviewButton().click();
    await resultCard().waitFor({ timeout: AI_TIMEOUT_MS });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check("mobile: khong tran ngang", overflow <= 1, `overflow=${overflow}px`);
    const box = await resultCard().boundingBox();
    check("mobile: panel nam trong man hinh", box !== null && box.x >= 0 && box.x + box.width <= 391,
      box ? `x=${box.x.toFixed(0)} w=${box.width.toFixed(0)}` : "");
    await resultCard().scrollIntoViewIfNeeded();
    await shot(page, "10-mobile");
    await page.setViewportSize({ width: 1440, height: 900 });

    // ── 7. Gọi API trực tiếp (không qua UI) ────────────────────────────
    const auth = { Authorization: `Bearer ${token}` };
    const notAccepted = await api.post(`${API}/submissions/${wrongSubmission.id}/ai-review`, { headers: auth });
    check("API: bai sai -> 409 SUBMISSION_NOT_ACCEPTED",
      notAccepted.status() === 409 && (await notAccepted.json()).error_code === "SUBMISSION_NOT_ACCEPTED");

    const noToken = await api.post(`${API}/submissions/${acceptedId}/ai-review`);
    check("API: khong token -> 401", noToken.status() === 401, String(noToken.status()));

    const other = await apiLogin(api, OTHER_STUDENT_EMAIL);
    if (other.token) {
      const foreign = await api.post(`${API}/submissions/${acceptedId}/ai-review`, {
        headers: { Authorization: `Bearer ${other.token}` },
      });
      check("API: bai cua sinh vien khac -> 404", foreign.status() === 404, String(foreign.status()));
    } else {
      check("API: dang nhap sinh vien thu hai", false, OTHER_STUDENT_EMAIL);
    }

    const oldEndpoint = await api.post(`${API}/ai/review`, {
      headers: auth,
      data: { code: "print(1)", language: "python" },
    });
    check("API: endpoint cu /ai/review da go", [404, 405].includes(oldEndpoint.status()), String(oldEndpoint.status()));
  } catch (error) {
    check("khong co exception", false, String(error));
    await shot(page, "99-exception").catch(() => {});
  } finally {
    const unexpected = consoleErrors.filter((text) => !/409|404|503/.test(text));
    check("khong co loi console/pageerror", unexpected.length === 0, unexpected.slice(0, 3).join(" | "));
    await api.dispose();
    await browser.close();
  }

  console.log("=".repeat(100));
  console.log(`KET QUA: ${passed} PASS, ${failed} FAIL  (anh: ${SHOTS})`);
  process.exit(failed === 0 ? 0 : 1);
}

main();
