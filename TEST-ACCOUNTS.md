# Tài khoản test

Hệ thống đã chạy thành công tại:

- **Frontend**: http://localhost:3000
- **Backend**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs
- **Judge0** (docker compose): http://localhost:2358
- **Ollama** (AI review): http://127.0.0.1:11434 — model `qwen2.5-coder:7b`

> **Lưu ý về Judge0**: mặc định dùng Judge0 local trong `docker-compose.yml`.
> Nếu muốn trỏ sang instance trên AWS/VPS, sửa `backend/.env`:
>
> ```env
> JUDGE0_API_URL=https://utc2-judge0.duckdns.org
> JUDGE0_API_TOKEN=<token>
> ```
>
> Backend đọc cả hai nhóm tên biến (`JUDGE0_URL`/`JUDGE0_AUTH_TOKEN` và
> `JUDGE0_API_URL`/`JUDGE0_API_TOKEN`), nhóm chuẩn được ưu tiên. Xem
> [docs/judge0-setup.md](docs/judge0-setup.md).

---

## Mật khẩu chung

```
Password@123
```

---

## Tài khoản sinh viên

### 1. Sinh viên chính (đầy đủ tình huống test)

- **Email**: `6751071001@st.utc2.edu.vn`
- **Họ tên**: Đặng Minh Demo
- **Lớp**: CQ.67.CNTT
- **Mô tả**: Có bài nộp với đủ 8 trạng thái:
  - ✅ Accepted (Đúng)
  - ❌ Wrong Answer (Sai)
  - 🔴 Compile Error (Lỗi biên dịch)
  - 💥 Runtime Error (Lỗi chạy)
  - ⏱️ Time Limit Exceeded (Quá thời gian)
  - ⏳ Pending (Đang chấm)
  - ⚠️ Internal Error (Lỗi hệ thống)
  - ❗ Error (Lỗi kết nối)

### 2. Sinh viên cùng lớp (test danh sách nhiều người)

- **Email**: `6751071003@st.utc2.edu.vn`
- **Họ tên**: Trần Văn Bạn Học
- **Lớp**: CQ.67.CNTT
- **Mô tả**: Có một vài bài nộp (để test hiển thị danh sách nhiều sinh viên trong lớp)

### 3. Sinh viên không có lớp (test empty state)

- **Email**: `6751071002@st.utc2.edu.vn`
- **Họ tên**: Nguyễn Thị Trống
- **Lớp**: Không có
- **Mô tả**: Không tham gia lớp nào, dùng để test trạng thái rỗng (empty state)

---

## Tài khoản giáo viên

- **Email**: `1111111117@st.utc2.edu.vn`
- **Họ tên**: Giảng Viên Demo
- **Vai trò**: Chủ khoá học demo

---

## Khoá học demo

### Khoá 1: DEMO101-2026A (HK1 2026-2027)

**Tên**: Lập trình Demo (đầy đủ tình huống)  
**Trạng thái**: Đang diễn ra

**Các buổi học:**

- Buổi 1, 2: **Đang mở** (open)
- Buổi 3: **Sắp tới** (upcoming)
- Buổi 4: **Đã kết thúc** (closed)

**Bài tập đặc biệt:**

- `DEMO_NO_TC`: Bài không có testcase (để test nhánh lỗi khi nộp bài)
- `DEMO_LOCKED`: Bài chưa mở (sinh viên không thấy trong danh sách)

**Các bài tập thông thường:**

- Tổng hai số (easy)
- Tính giai thừa (easy)
- Kiểm tra số nguyên tố (medium)
- Đảo ngược mảng (medium)
- Sắp xếp mảng tăng dần (hard)
- Bài của buổi sắp tới (easy)
- Bài của buổi đã kết thúc (medium)

### Khoá 2: DEMO102-2025B (HK2 2025-2026)

**Tên**: Cấu trúc dữ liệu Demo (học kỳ trước)  
**Trạng thái**: Đã kết thúc  
**Mục đích**: Test filter học kỳ, năm học và tìm kiếm trên dashboard

**Các bài tập:**

- In Hello World (easy)
- Tổng các phần tử mảng (easy)

---

## Các tình huống test được phủ

✅ Dashboard sinh viên với nhiều lớp  
✅ Lọc theo học kỳ và năm học  
✅ Tìm kiếm theo mã/tên lớp  
✅ Buổi học ở nhiều trạng thái (open/upcoming/closed)  
✅ Bài tập nhiều cấp độ (easy/medium/hard)  
✅ Bài tập có/không có testcase mẫu  
✅ Bài tập chưa mở (không hiển thị với sinh viên)  
✅ Bài nộp với đủ 8 trạng thái verdict  
✅ Empty state (sinh viên không có lớp)  
✅ Nhiều ngôn ngữ (Python, C, C++, Java, JavaScript)  
✅ Chấm code thật qua Judge0 local (đủ 5 loại kết quả)  
✅ AI Review đa ngôn ngữ (VI/EN) với Ollama local, có cache theo từng ngôn ngữ  

---

## Kiểm thử nhanh sau khi bật hệ thống

```powershell
# 1. Judge0 còn sống?
curl.exe -s http://localhost:2358/about

# 2. Chấm thử đủ ngôn ngữ + trạng thái kết quả (15 assertion)
cd backend; python -m tools.live_judge_check

# 3. Luồng sinh viên end-to-end: nộp bài -> Judge0 -> kết quả (41 assertion)
cd backend; python -m tools.e2e_student_flow

# 4. AI Review end-to-end với Ollama thật, cả VI và EN (16 assertion)
cd backend; python -m tools.e2e_ai_review

# 5. Bài "chạy được nhưng chưa tối ưu" -> AI phải gợi ý tối ưu
cd backend; python -m tools.check_review_optimizable
```

> Cần backend (`uvicorn app.main:app --port 8000`) và Ollama đang chạy cho
> các bước 3–5.

---

## Ghi chú

- Dữ liệu được tính **tương đối** so với ngày hiện tại, nên luôn hợp lệ khi chạy script
- Tất cả tài khoản đã bỏ qua yêu cầu đổi mật khẩu lần đầu (`must_change_password=False`)
- Để seed lại từ đầu: `python -m tools.seed_demo_data --reset`
