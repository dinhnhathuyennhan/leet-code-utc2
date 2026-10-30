# Hướng dẫn upgrade database schema local

Tài liệu này hướng dẫn upgrade database PostgreSQL local sau khi nhánh đổi schema được merge vào `develop`. Các bước tạo backup, restore sang database clone, thử migration trên clone, rồi mới upgrade database chính.

## 0. Điều kiện và quy tắc an toàn

- Ví dụ bên dưới theo cấu hình Docker Compose của repo: container `cham-code-db`, database chính `ChamCodeDB`, user `chamcode`, port `5432`.
- Chạy lệnh Alembic từ thư mục `backend`, trong virtualenv của backend.
- Xác nhận `.env` trỏ tới đúng DB local. Xem các giá trị không bí mật bằng:

  ```powershell
  Get-Content ..\.env | Where-Object { $_ -match '^DB_(SERVER|PORT|NAME|USER)=' }
  ```

- Nếu DB host/name khác ví dụ, container không đúng, hoặc Alembic báo revision khác dự kiến, **dừng lại** và điều chỉnh hướng dẫn cho đúng môi trường. Không chạy lệnh upgrade khi chưa xác nhận DB đích.
- Không chạy code backend mới với database chưa upgrade. Tạm dừng API hoặc các tiến trình đang ghi vào DB trong lúc cutover.
- Backup chứa dữ liệu thật: lưu ở nơi an toàn, ngoài repo; không commit hoặc gửi file này lên chat.
- UUID migration không hỗ trợ downgrade. Nếu cần rollback sau migration, phải restore backup.

## 1. Xác nhận trạng thái database chính
- Đứng tại thư mục gốc của dự án
```powershell
cd backend
alembic current
```

Trước khi upgrade, database chính trong quy trình này cần ở revision `b9804d25ccef`. Repo cần có một head là `e6f7a8b9c0d1`:

```powershell
alembic heads
```

Nếu revision hiện tại không phải `b9804d25ccef`, không tiếp tục theo tài liệu này cho tới khi xác định được lịch sử migration của DB.

## 2. Tạo backup database chính
Lưu ý: các lệnh dưới đây phù hợp với PowerShell nên chuyển trước khi thực thi lệnh

Tạo tên file mới có timestamp để tránh ghi đè backup cũ:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dumpName = "ChamCodeDB-before-schema-$stamp.dump"
$containerDump = "/tmp/$dumpName"
$backupFile = Join-Path $env:USERPROFILE "db-backups\$dumpName"

New-Item -ItemType Directory -Force "$env:USERPROFILE\db-backups"
docker exec cham-code-db pg_dump -U chamcode -d ChamCodeDB -Fc -f $containerDump
docker cp "cham-code-db:$containerDump" $backupFile
docker exec cham-code-db pg_restore -l $containerDump
```

Chỉ tiếp tục khi `pg_dump`, `docker cp` và `pg_restore -l` thành công, đồng thời file `$backupFile` tồn tại.

## 3. Tạo database clone và restore backup

Tên clone dùng chữ thường để tránh PostgreSQL tự chuyển tên identifier không đặt trong dấu nháy thành chữ thường. Clone mẫu là `chamcodedb_schema_clone`.

```powershell
docker exec cham-code-db psql -U chamcode -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE chamcodedb_schema_clone OWNER chamcode;"
docker cp $backupFile "cham-code-db:/tmp/$dumpName"
docker exec cham-code-db pg_restore -U chamcode -d chamcodedb_schema_clone --no-owner --exit-on-error --single-transaction "/tmp/$dumpName"
```

Nếu `CREATE DATABASE` báo clone đã tồn tại, dừng lại; không xóa database hiện có. Chọn một tên clone mới, viết chữ thường, rồi dùng tên đó nhất quán trong các lệnh tiếp theo.

Kiểm tra clone có đúng database/schema và Alembic revision trước khi migration:

```powershell
docker exec cham-code-db psql -U chamcode -d chamcodedb_schema_clone -c "SELECT current_database(), current_schema();"
docker exec cham-code-db psql -U chamcode -d chamcodedb_schema_clone -c "SELECT version_num FROM alembic_version;"
```

Revision clone phải là `b9804d25ccef`.

### So sánh số dòng trước migration

Chạy truy vấn trên clone:

```powershell
@'
SELECT
  (SELECT count(*) FROM public."user") AS users,
  (SELECT count(*) FROM public.course) AS courses,
  (SELECT count(*) FROM public.enrollment) AS enrollments,
  (SELECT count(*) FROM public.submission) AS submissions;
'@ | docker exec -i cham-code-db psql -U chamcode -d chamcodedb_schema_clone -v ON_ERROR_STOP=1
```

Chạy lại với `-d ChamCodeDB` để kiểm tra database chính. Các số phải khớp. Mỗi thành viên có thể có số liệu khác nhau; ví dụ khi quy trình này được thử trong môi trường tác vụ.

## 4. Upgrade clone bằng Alembic

Trong PowerShell ở thư mục `backend`, tạm thời đặt `DB_NAME` để chỉ Alembic vào clone. Không sửa `.env` lâu dài.

```powershell
$previousDbName = $env:DB_NAME
$env:DB_NAME = "chamcodedb_schema_clone"
alembic current
```

Chỉ tiếp tục nếu lệnh trên báo `b9804d25ccef`:

```powershell
alembic upgrade head
alembic current
```

Revision cuối phải là `e6f7a8b9c0d1`. Sau khi hoàn tất clone test, khôi phục biến môi trường:

```powershell
if ($null -eq $previousDbName) {
    Remove-Item Env:DB_NAME -ErrorAction SilentlyContinue
} else {
    $env:DB_NAME = $previousDbName
}
```

## 5. Kiểm tra clone sau migration

### Không còn student thiếu/sai MSSV

```powershell
@'
SELECT count(*) AS invalid_students
FROM public."user"
WHERE role_id = 3
  AND (student_code IS NULL OR student_code !~ '^[0-9]{10}$');
'@ | docker exec -i cham-code-db psql -U chamcode -d chamcodedb_schema_clone -v ON_ERROR_STOP=1
```

`invalid_students` phải bằng `0`.

### Không có foreign key mồ côi

```powershell
@'
SELECT
  (SELECT count(*) FROM public.course c
   LEFT JOIN public."user" u ON u.user_id = c.created_by
   WHERE u.user_id IS NULL) AS courses_without_creator,
  (SELECT count(*) FROM public.enrollment e
   LEFT JOIN public."user" u ON u.user_id = e.student_id
   WHERE u.user_id IS NULL) AS enrollments_without_user,
  (SELECT count(*) FROM public.submission s
   LEFT JOIN public."user" u ON u.user_id = s.student_id
   WHERE u.user_id IS NULL) AS submissions_without_user;
'@ | docker exec -i cham-code-db psql -U chamcode -d chamcodedb_schema_clone -v ON_ERROR_STOP=1
```

Cả ba kết quả phải bằng `0`.

### Đối chiếu số dòng sau migration

Chạy lại truy vấn đếm ở bước 3 trên clone và DB chính. Số dòng của `user`, `course`, `enrollment`, `submission` phải không đổi. Kiểm tra kiểu `user.user_id` đã là `uuid`:

Các lệnh kiểm tra ở phần này đang nhắm vào clone. Khi kiểm tra DB chính sau upgrade, đổi `-d chamcodedb_schema_clone` thành `-d ChamCodeDB`.

```powershell
docker exec cham-code-db psql -U chamcode -d chamcodedb_schema_clone -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user' AND column_name IN ('user_id', 'student_code', 'date_of_birth') ORDER BY column_name;"
```

`user_id` cần có kiểu `uuid`; `student_code` cần tồn tại; `date_of_birth` không còn xuất hiện.

Sau các kiểm tra dữ liệu, chạy backend trỏ vào clone và smoke test đăng nhập, refresh token, danh sách submission. Không tiếp tục nếu migration báo lỗi, số dòng thay đổi, MSSV còn thiếu/sai, hoặc foreign key có bản ghi mồ côi.

## 6. Upgrade database chính

Chỉ thực hiện sau khi clone qua các kiểm tra. Dừng backend/các tiến trình đang ghi dữ liệu và tạo **backup mới ngay trước cutover** bằng các lệnh ở bước 2.

Đặt Alembic về đúng database chính và xác nhận revision trước khi upgrade:

```powershell
$previousDbName = $env:DB_NAME
$env:DB_NAME = "ChamCodeDB"
alembic current
```

Chỉ tiếp tục nếu `alembic current` báo `b9804d25ccef`:

```powershell
alembic upgrade head
alembic current
```

Revision cuối cần là `e6f7a8b9c0d1`. Chạy lại các kiểm tra MSSV, foreign key và số dòng ở bước 5 trên `ChamCodeDB`. Sau đó khởi động backend dùng code UUID mới và kiểm tra các luồng chính.

Khôi phục biến môi trường PowerShell:

```powershell
if ($null -eq $previousDbName) {
    Remove-Item Env:DB_NAME -ErrorAction SilentlyContinue
} else {
    $env:DB_NAME = $previousDbName
}
```

Việc đổi `user_id` tạo UUID mới, nên token đăng nhập cũ có thể không còn hợp lệ; người dùng cần đăng nhập lại. Nếu cần rollback migration UUID, restore backup phù hợp thay vì chạy downgrade.
