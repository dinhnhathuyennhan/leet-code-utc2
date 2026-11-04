# Thiết kế giao diện — AI Review code

## Mục tiêu (theo yêu cầu của leader)

1. **Chỉ hiện nút "Review code" khi bài nộp đã pass hết testcase.** Code chưa đúng thì không review.
2. **Chỉ khi sinh viên nhấn nút mới gửi prompt cho AI.** Không tự động gọi AI sau khi chấm.
3. **AI đưa ra hướng cải thiện tối ưu, không gợi ý cách làm bài.** Code đã đúng, AI chỉ nhận xét hiệu năng.

Ví dụ: bài kiểm tra số nguyên tố, sinh viên duyệt ước từ 2 tới `n-1`, vẫn pass hết test. AI review chỉ ra độ phức tạp hiện tại là `O(n)` và hướng tối ưu là chỉ cần duyệt tới `sqrt(n)`, đạt `O(sqrt(n))`.

## Luồng sử dụng

```
Sinh viên nộp bài
      │
      ▼
Judge0 chấm (pending → processing → kết quả)
      │
      ├── Chưa pass hết testcase (wrong_answer, compile_error, ...)
      │       → Không có nút Review code
      │
      └── status = accepted VÀ passed_count = total_testcases
              → Hiện nút "Review code"
                      │  (sinh viên nhấn)
                      ▼
              Gửi code của BÀI NỘP ĐÓ cho AI → hiện kết quả review
```

Điều kiện hiện nút: `status === "accepted" && total_testcases > 0 && passed_count === total_testcases`.

## Vị trí trên giao diện

| # | Màn hình | File | Khi nào có nút |
|---|---|---|---|
| 1 | Làm bài | `student/classes/[id]/assignments/[assignmentId]/page.tsx` | Trong khối "Kết quả chấm", ngay sau khi lần nộp vừa rồi pass hết |
| 2 | Chi tiết bài nộp | `student/submissions/[id]/page.tsx` | Khi bài nộp đó pass hết (xem lại review cho bài nộp cũ) |

Code gửi cho AI luôn là **code của bài nộp đã pass**, không phải code đang gõ trong editor. Nếu sinh viên sửa code sau khi nộp, phải nộp lại và pass thì mới review được bản mới.

### Màn hình 1: Trang làm bài

```
┌─ Kết quả chấm ─────────────────────────────────────────────────────────┐
│ ✓ Accepted                                               10.0/10       │
│ Đạt 12/12 test · Nộp lúc 16:30 · Python                                │
│                                                                        │
│ Bài đã pass toàn bộ testcase. Xem AI nhận xét về hiệu năng code?       │
│                                                     [✦ Review code]    │
└────────────────────────────────────────────────────────────────────────┘
┌─ ✦ AI Review ──────────────────────────────────────────────────────────┐
│ (panel kết quả, chỉ xuất hiện sau khi nhấn nút)                        │
└────────────────────────────────────────────────────────────────────────┘
```

- Kết quả `wrong_answer`, `compile_error`, `runtime_error`, `time_limit_exceeded`... hiện như hiện tại, **không** có nút, **không** có dòng nhắc về AI.
- Nộp bài mới thì xoá review của lần nộp trước.

### Màn hình 2: Chi tiết bài nộp

Nút "Review code" đặt ở thanh tiêu đề khối "Mã nguồn đã nộp"; panel hiện ngay dưới khối mã nguồn. Bài nộp không pass hết thì không có nút.
## Panel kết quả `AiReviewPanel`

Ví dụ với bài số nguyên tố duyệt tới `n-1`:

```
┌─ ✦ AI Review ──────────────────────────────────────────────── [Đóng ✕] ┐
│ Code đúng nhưng duyệt mọi số từ 2 tới n-1 để tìm ước.                  │
│                                                                        │
│ ┌─ Thời gian ──────────────┐  ┌─ Bộ nhớ ─────────────────┐             │
│ │ O(n)  →  O(sqrt(n))      │  │ O(1)                     │             │
│ └──────────────────────────┘  └──────────────────────────┘             │
│ Giải thích: Vòng lặp chạy n-2 lần trong trường hợp xấu nhất...         │
│                                                                        │
│ ⚠ Điểm chưa tối ưu                                                     │
│   • Duyệt quá số lần cần thiết: nếu n có ước lớn hơn sqrt(n) thì       │
│     cũng có ước nhỏ hơn sqrt(n)                                        │
│                                                                        │
│ 💡 Hướng cải thiện                                                      │
│   Chỉ cần kiểm tra ước từ 2 tới sqrt(n)                                │
│                                                                        │
│ ⓘ Nhận xét do AI tạo, có thể chưa chính xác. Không ảnh hưởng tới điểm. │
└────────────────────────────────────────────────────────────────────────┘
```

| Phần | Field backend | Quy tắc hiển thị |
|---|---|---|
| Tóm tắt | `summary` | Dòng đầu panel |
| Thẻ Thời gian / Bộ nhớ | `time_complexity`, `space_complexity`, `optimization.expected_*` | Hiện `trước → sau` chỉ khi `is_optimizable = true` và giá trị sau khác giá trị trước. Font mono |
| Giải thích | `complexity_explanation` | Đoạn văn dưới 2 thẻ |
| Điểm chưa tối ưu | `issues` | Mảng rỗng → dòng xanh "Không phát hiện điểm chưa tối ưu" |
| Hướng cải thiện | `optimization.suggestion` | `is_optimizable = false` → khối xanh "Code đã ở mức tối ưu hợp lý" |
| Chú thích | — | Luôn hiện |

Mọi chuỗi hiển thị dạng text thuần (`whitespace-pre-wrap`), không render HTML/Markdown. Màu theo `GradingResultPanel`: viền tím, điểm chưa tối ưu `amber`, tối ưu `emerald`, lỗi `red`, có dark mode.

## Các trạng thái

| Trạng thái | Giao diện |
|---|---|
| Bài chưa pass hết | Không có nút, không có panel |
| Pass hết, chưa nhấn | Chỉ có nút "Review code" |
| Đang review | Nút chuyển "Đang review…" + spinner, bị disable. Panel hiện skeleton. Sau 15 giây hiện thêm "Lần đầu có thể mất 1–2 phút do AI đang khởi động" |
| Thành công | Panel kết quả |
| Lỗi | Panel viền đỏ: `message` từ backend + nút "Thử lại" |

Thông báo lỗi lấy từ `message` của backend:

| Status | error_code | Thông báo |
|---|---|---|
| 503 | `AI_BUSY` | AI đang phân tích bài khác, vui lòng thử lại sau |
| 503 | `AI_UNAVAILABLE` | Không thể kết nối AI Server |
| 504 | `AI_TIMEOUT` | AI xử lý quá thời gian cho phép |
| 502 | `AI_INVALID_RESPONSE` | AI trả về dữ liệu không hợp lệ |

## Quy tắc hành vi

1. **Chỉ gọi AI khi nhấn nút.** Không gọi tự động khi chấm xong, không gọi lại tự động khi lỗi.
2. **Không gọi trùng:** đang review thì nút bị disable.
3. **Timeout client `200_000` ms** cho request này (backend chờ Ollama tối đa 180 giây; mặc định client 10 giây sẽ cắt trước).
4. **Không lưu:** kết quả chỉ nằm trong state trang, rời trang là mất.
5. **Accessibility:** panel có `aria-live="polite"`, đang chạy đặt `aria-busy="true"`, nút có nhãn chữ.

## Ngôn ngữ của nội dung review (VI/EN)

Nội dung review (summary, giải thích, issues, suggestion) do model sinh ra, nên
ngôn ngữ phải do prompt quyết định — **không dịch ở client** (review là văn xuôi
kỹ thuật, dịch máy sẽ sai thuật ngữ và không đồng bộ với Big O).

`POST /ai/review/{submission_id}` nhận body tuỳ chọn `{"locale": "vi" | "en"}`.
Backend chọn `SYSTEM_PROMPTS[locale]` ở `app/modules/ai_review/prompts.py`; body
rỗng hoặc không gửi (client cũ) dùng `"vi"`. `locale` **không** ảnh hưởng code
đem đi review — code vẫn lấy từ DB theo `submission_id`.

Luồng phía client (`ai-review-panel.tsx`):

| Tình huống | Hành vi |
|---|---|
| Lần đầu bấm "Review code" | Gửi `locale` đang xem (VI hoặc EN) |
| Chưa bấm review mà đổi ngôn ngữ | Không gọi AI (chưa có gì để review) |
| Đã review, đổi ngôn ngữ, ngôn ngữ đích **chưa có** kết quả | Gọi AI lại bằng ngôn ngữ mới, panel hiện skeleton trong lúc chờ |
| Đã review, đổi ngôn ngữ, ngôn ngữ đích **đã có** kết quả | Hiện ngay bản đã lưu, không chờ Ollama |
| Chuyển qua chuyển lại liên tục | Mỗi ngôn ngữ chỉ gọi AI **một lần**; các lần sau lấy từ cache |
| Đóng panel rồi đổi ngôn ngữ | Panel không bật lại; kết quả của cả hai ngôn ngữ bị xoá |
| Ngôn ngữ đích đang chạy mà quay lại ngôn ngữ cũ | Hiện ngay kết quả cũ; lượt đang chạy vẫn tiếp tục ở nền |

Cách làm: mỗi ngôn ngữ là **một `useMutation` riêng** (`useAiReview(submissionId, locale)`).
`mutationKey` gồm cả `locale` nên React Query giữ state độc lập cho "vi" và "en" —
kết quả, lỗi, và cả lượt đang chạy đều được cache theo từng ngôn ngữ.


## API backend

Có hai route AI review:

### 1. `POST /ai/review/{submission_id}` — của sinh viên (feature này)

- **Quyền:** chỉ Student, và chỉ bài nộp của chính mình.
- **Request body:** tuỳ chọn `{"locale": "vi" | "en"}` — chỉ chọn ngôn ngữ của nội dung review. Code, ngôn ngữ lập trình, đề bài và ràng buộc đều lấy từ DB theo `submission_id`, client không gửi code được. Body rỗng dùng mặc định `"vi"`.
- **Điều kiện:** `status = "accepted"`, bài có ít nhất 1 testcase và `passed_count >= total_number_testcase`.
- **Prompt** (`backend/app/modules/ai_review/prompts.py`): báo cho AI rằng code đã pass toàn bộ testcase; chỉ nhận xét hiệu năng; không bàn tính đúng sai, không viết lời giải, không chèn code; code đã tối ưu thì `is_optimizable = false` và `issues = []`; luôn trả lời tiếng Việt. Đề bài và ràng buộc được gửi kèm để AI đánh giá theo giới hạn input.

**Response 200:** `AIReviewResponse` như bảng ở mục [Panel kết quả](#panel-kết-quả-aireviewpanel).

**Lỗi:**

| Status | error_code | Khi nào | UI |
|---|---|---|---|
| 403 | `FORBIDDEN` | Người gọi không phải Student | Không xảy ra trên UI sinh viên |
| 404 | `NOT_FOUND` | Bài nộp không tồn tại hoặc của người khác | Thông báo lỗi |
| 409 | `SUBMISSION_NOT_ACCEPTED` | Bài chưa pass hết testcase | Không xảy ra nếu UI ẩn nút đúng điều kiện |
| 422 | `CODE_TOO_LONG` | Code đã nộp dài hơn 15.000 ký tự | Thông báo lỗi, không có nút Thử lại |
| 502/503/504 | `AI_*` | Lỗi phía AI (bảng ở mục trên) | Thông báo + nút Thử lại |

### 2. `POST /ai/review` — review code tuỳ ý (admin/teacher, có sẵn ở develop)

- **Quyền:** `ADMIN`, `TEACHER`, `STUDENT` (role khác bị chặn 403 `FORBIDDEN`).
- **Request body:** `{"code": "...", "language": "python"}` — giữ đúng shape như develop.
- **Prompt:** dùng `SYSTEM_PROMPT` trung tính của develop (`prompts.py`), **không** giả định code đã pass testcase (code do client gửi lên, chưa chắc đã được chấm). Luôn trả về tiếng Việt.
- Route này không nằm trong phạm vi feature sinh viên — giữ lại để không phá chức năng của phần admin.

Kết quả chạy thật với `qwen2.5-coder:7b`:
- Bài số nguyên tố duyệt tới `n-1`: AI trả `O(n) → O(sqrt(n))`, đề xuất chỉ duyệt ước tới `sqrt(n)`.
- Two Sum dùng hash map (đã tối ưu): AI trả `is_optimizable = false`, `issues = []`.

## i18n

Thêm key nhóm `aiReview.*` vào `frontend/src/lib/i18n/dictionary.ts`:

| Key | vi | en |
|---|---|---|
| `aiReview.button` | Review code | Review code |
| `aiReview.prompt` | Bài đã pass toàn bộ testcase. Xem AI nhận xét về hiệu năng code? | All testcases passed. Get AI feedback on performance? |
| `aiReview.running` | Đang review… | Reviewing… |
| `aiReview.warmup` | Lần đầu có thể mất 1–2 phút do AI đang khởi động | First run may take 1–2 minutes while the AI warms up |
| `aiReview.title` | AI Review | AI Review |
| `aiReview.time` | Thời gian | Time |
| `aiReview.space` | Bộ nhớ | Space |
| `aiReview.explanation` | Giải thích | Explanation |
| `aiReview.issues` | Điểm chưa tối ưu | Inefficiencies |
| `aiReview.noIssues` | Không phát hiện điểm chưa tối ưu | No inefficiencies found |
| `aiReview.optimization` | Hướng cải thiện | How to improve |
| `aiReview.alreadyOptimal` | Code đã ở mức tối ưu hợp lý | Code is already reasonably optimal |
| `aiReview.disclaimer` | Nhận xét do AI tạo, có thể chưa chính xác. Không ảnh hưởng tới điểm. | AI-generated, may be inaccurate. Does not affect your grade. |
| `aiReview.retry` | Thử lại | Retry |

## Cấu trúc code đề xuất

| File | Nội dung |
|---|---|
| `lib/types/ai-review.ts` | `AiReviewResponse` khớp schema backend |
| `lib/api/endpoints/ai-review.ts` | Hàm gọi review (kèm `locale`), `timeout: 200_000` |
| `lib/hooks/use-ai-review.ts` | `useMutation` React Query, key gồm `locale` để cache riêng từng ngôn ngữ |
| `lib/helpers/submission-status.ts` | Thêm `canReviewCode(submission)` theo điều kiện ở trên |
| `components/student/ai-review-panel.tsx` | Nút + panel + các trạng thái + cache kết quả theo ngôn ngữ |
| `components/student/ai-review-panel.test.tsx` | Test: không có nút khi chưa pass hết; có nút khi pass hết; chưa nhấn thì không gọi API; hiển thị `trước → sau`; trạng thái lỗi; cache và sinh lại theo ngôn ngữ |

## Ngoài phạm vi

- Giao diện cho Giáo viên/Admin.
- Lưu lịch sử review, giới hạn số lần review theo sinh viên.
- Tắt review theo bài hoặc khi đang thi.
