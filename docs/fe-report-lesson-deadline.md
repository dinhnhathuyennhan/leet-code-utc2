# Báo cáo cho FE: hạn bài tập lấy theo ngày của buổi học

Nhánh backend: `fix/sync-problem-deadline-with-lesson`

## Lỗi đã sửa ở backend

Trước đây, đổi ngày của buổi học (`PATCH /courses/{course_id}/lessons/{lesson_id}`) không làm đổi hạn của các bài tập trong buổi:

- Server vẫn cho nộp, hoặc chặn nộp, theo hạn cũ.
- Trong khi đó giao diện lại hiện hạn mới, vì hạn hiển thị lấy từ ngày của buổi.

## Quy tắc mới

1. **Ngày của buổi học là nguồn chuẩn cho hạn bài tập.** Mọi bài trong buổi đều theo khung giờ (giờ VN):
   - mở lúc **00:00** ngày `start_date`
   - đóng lúc **23:59:59** ngày `end_date`
2. **Đổi `start_date`/`end_date` của buổi học:** server tự ghi đè `start_datetime`/`end_datetime` của mọi bài trong buổi theo khung trên.
   - Giờ riêng của từng bài (ví dụ 09:00–11:30) sẽ bị ghi đè.
   - Nếu gửi lại đúng ngày cũ, hoặc chỉ đổi tên buổi, thì lịch của bài không bị đụng tới.
3. **Đồng bộ chỉ đi một chiều Lesson → Problem.** Với **bài thuộc buổi học**, `PATCH /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}` **bỏ qua** `start_datetime`/`end_datetime`:
   - Server không báo lỗi, nhưng cũng không lưu hai trường này.
   - Các trường khác (title, description...) vẫn được cập nhật bình thường.
   - Sửa bài cũng không làm đổi ngày của buổi.
   - Ngoại lệ duy nhất vẫn bị báo lỗi: datetime gửi lên **thiếu múi giờ**, vì schema vẫn kiểm tra offset. FE hiện luôn gửi kèm `+07:00` nên không bị ảnh hưởng.
   - Cũng vì bị bỏ qua, server không còn kiểm tra `start < end` cho bài thuộc buổi.
4. **Bài trong ngân hàng đề** (chưa gắn buổi nào) vẫn sửa được `start_datetime`/`end_datetime` như cũ. Khi gắn vào buổi, bài sẽ nhận lịch của buổi.

## Contract API không đổi

- Response vẫn có `start_datetime`/`end_datetime` cho từng bài, giá trị luôn khớp với ngày của buổi.
- Request gửi kèm hai trường này cũng không lỗi.

→ FE hiện tại **không bị gãy**. Phần dưới đây là dọn dẹp để giao diện không còn cho nhập những giá trị mà server sẽ bỏ qua.

## FE cần sửa

| File | Việc cần làm |
|---|---|
| `src/components/teacher/session-edit-page.tsx` | Bỏ state `openTime`/`closeTime` (dòng 49-50), validate giờ (dòng 65-66) và các ô nhập giờ mở/đóng trong modal "Thêm bài tập thủ công". Bỏ lời gọi `updateProblem(... start_datetime, end_datetime)` ở dòng 90, cùng `getSessionDetail` thứ hai ở dòng 91-92, vì server đã tự gán lịch của buổi khi gắn bài. `createBankProblem` (dòng 85) vẫn cần gửi `start_datetime`/`end_datetime` vì schema tạo bài ngân hàng bắt buộc, có thể gửi cố định như `problem-bank-page.tsx:72`. |
| `src/components/teacher/session-problem-editor.tsx` | Bỏ `start_datetime`/`end_datetime` khỏi `Draft` (dòng 25, 48-49), bỏ validate (dòng 107), bỏ khỏi payload (dòng 123) và bỏ ô nhập ở dòng 181. Hạn chỉ hiển thị dạng đọc, theo `lessonStartDate`/`lessonEndDate`, ví dụ: "Mở 00:00 dd/mm – Hạn 23:59 dd/mm". |
| `src/components/admin/admin-problem-editor.tsx` | Khi sửa bài **thuộc buổi** (từ `admin-problem-detail.tsx`, hoặc `admin-bank-problem-detail.tsx` với `attached`), ẩn hoặc khoá ô `start`/`end`: state ở dòng 40-41, validate ở dòng 54, payload ở dòng 70, ô nhập ở dòng 90-91. Bài ngân hàng giữ nguyên. |
| `src/components/admin/admin-bank-problem-detail.tsx` | Dòng 34-35 và 121: nếu `attached` thì không cần gửi diff `start_datetime`/`end_datetime`. Dòng 114 (legacy editor) gọi `updateAdminProblem` với toàn bộ `data`, cũng không cần kèm lịch. |
| `src/components/teacher/session-edit-page.tsx:201-203`, `src/components/teacher/session-editor-dialog.tsx:83-85` (lưu ngày buổi) | Hiện mới invalidate `courseKeys.detail`. Cần invalidate hoặc gọi lại cả dữ liệu `getSessionDetail` để danh sách bài hiện lịch mới. Có thể hiện cảnh báo: "Đổi ngày buổi học sẽ cập nhật hạn của tất cả bài tập trong buổi." |
| `src/lib/types/course.ts`, `src/lib/types/admin.ts` | Có thể đánh dấu `start_datetime`/`end_datetime` của bài trong buổi là chỉ đọc (read-only). Không bắt buộc. |

## Dữ liệu cũ đã lệch

- Server chỉ đồng bộ khi ngày của buổi **thực sự đổi**.
- Các bài bị lệch lịch từ trước khi deploy sẽ không tự được sửa, kể cả khi bấm lưu lại form với ngày cũ.
- DB hiện chỉ có dữ liệu test, nên cách xử lý là chạy lại seed hoặc reset DB. Cách khác là đổi ngày của buổi đi rồi đổi lại.

## Cách kiểm tra sau khi FE sửa

1. Giáo viên dời `end_date` của buổi về hôm qua, rồi sinh viên nộp bài: phải thấy "Bài tập đã hết hạn nộp".
2. Gia hạn `end_date` ra tương lai: nộp lại được, và hạn hiển thị trên cả màn của giáo viên lẫn sinh viên đều đổi theo.
3. Thêm bài mới vào buổi: bài nhận đúng khung 00:00 → 23:59 của buổi, không còn ô nhập giờ.
