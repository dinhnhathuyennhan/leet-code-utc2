# Hướng dẫn dựng và chia sẻ Judge0

Mục tiêu: dựng Judge0 self-host, gửi code thử và nhận đúng 5 loại kết quả
(Accepted, Wrong Answer, Time Limit Exceeded, Compile Error, Runtime Error).
Xem bối cảnh trong [roadmap.md](roadmap.md).

## Bước 0: Kiểm tra máy mình thuộc trường hợp nào

Judge0 (bản 1.13.x) dùng sandbox `isolate` và **bắt buộc chạy trên cgroup v1**.

```bash
stat -fc %T /sys/fs/cgroup/   # cgroup2fs = đang dùng v2 | tmpfs = đang dùng v1
systemctl --version | head -1 # xem phiên bản systemd
```

| Kết quả | Cách làm |
|---|---|
| `tmpfs` (đã là v1) | Cài thẳng trên máy, bỏ qua bước 1 và 2, làm từ **bước 3** |
| `cgroup2fs` và systemd **≤ 255** (vd Ubuntu 22.04/24.04) | Có thể chuyển máy sang v1 bằng GRUB (xem [Phụ lục](#phụ-lục-chuyển-máy-thật-sang-cgroup-v1)) hoặc dùng VM như bên dưới |
| `cgroup2fs` và systemd **≥ 258** (vd Ubuntu 26.04) | **Bắt buộc dùng VM**, vì systemd ≥ 258 đã bỏ hẳn cgroup v1. Đừng sửa GRUB trên máy thật |
| Windows / macOS | Dùng VM (Multipass có bản cho cả 2 hệ điều hành) hoặc dùng Judge0 chung của nhóm |

> **Gợi ý cho nhóm:** chỉ cần **1 máy** (hoặc 1 VPS) chạy Judge0 cho cả nhóm dùng
> chung. Các bạn khác **không cần làm Bước 1–7**, chỉ cần làm theo
> [Chia sẻ Judge0 cho cả nhóm](#chia-sẻ-judge0-cho-cả-nhóm-tailscale), Phần B.

---

## Bước 1: Tạo VM Ubuntu 22.04 bằng Multipass

```bash
sudo snap install multipass
multipass launch 22.04 --name judge0 --cpus 4 --memory 4G --disk 20G
multipass shell judge0          # vào shell của VM
```

Các lệnh từ đây tới hết bước 4 đều chạy **bên trong VM**.

## Bước 2: Chuyển VM sang cgroup v1 và cài Docker

> Chạy **từng lệnh một**, lệnh trước xong mới dán lệnh sau. Dán nhiều dòng cùng lúc
> dễ bị dính dòng (vd thành `update-grubcurl: command not found`).

```bash
# 1. Thêm tham số kernel. Tạo file riêng để không bị file cấu hình của cloud image ghi đè.
#    Giữ nguyên $GRUB_CMDLINE_LINUX trong nháy đơn, GRUB sẽ tự xử lý biến này.
echo 'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX systemd.unified_cgroup_hierarchy=0"' | sudo tee /etc/default/grub.d/99-cgroup-v1.cfg

# 2. Cập nhật GRUB và kiểm tra, lệnh grep phải ra số > 0
sudo update-grub
grep -c 'unified_cgroup_hierarchy=0' /boot/grub/grub.cfg

# 3. Cài Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu

# 4. Khởi động lại VM
sudo reboot
```

Đợi khoảng 20 giây rồi `multipass shell judge0` lại, sau đó kiểm tra:

```bash
stat -fc %T /sys/fs/cgroup/   # phải ra: tmpfs
docker ps                     # chạy được mà không cần sudo
```

## Bước 3: Tải và cấu hình Judge0

> Vào https://github.com/judge0/judge0/releases xem bản mới nhất. **Dùng bản ≥ 1.13.1**
> vì các bản cũ hơn có lỗ hổng thoát sandbox (CVE-2024-28185, CVE-2024-28189, CVE-2024-29021).
> Nếu bản mới đã hỗ trợ cgroup v2 thì có thể bỏ qua bước 1–2.

> Dùng **Judge0 CE** (`judge0-v1.13.1.zip`), **không dùng bản Extra CE** (`-extra`).
> Bản Extra có bộ ngôn ngữ và `language_id` khác, không cần cho môn học.

```bash
sudo apt install -y unzip     # cloud image Ubuntu 22.04 thường chưa có unzip
wget https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip
unzip judge0-v1.13.1.zip
cd judge0-v1.13.1
```

Đặt mật khẩu trong `judge0.conf` (**bắt buộc**, để trống thì Judge0 không chạy):

```bash
# Sinh 2 mật khẩu ngẫu nhiên và ghi thẳng vào file
sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$(openssl rand -hex 16)/; s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 16)/" judge0.conf

# Kiểm tra: 2 dòng, mỗi dòng có một chuỗi hex phía sau dấu =
grep -E '^(REDIS|POSTGRES)_PASSWORD' judge0.conf
```

## Bước 4: Khởi động

```bash
docker compose up -d db redis
sleep 10                      # đợi DB và Redis sẵn sàng
docker compose up -d
sleep 5
docker compose ps             # server và workers phải ở trạng thái "running"

curl -s http://localhost:2358/about
```

## Bước 5: Gọi Judge0 từ máy thật

Thoát VM (`exit`) rồi lấy IP của VM:

```bash
multipass info judge0 | grep IPv4     # vd 10.92.x.x
export J0=http://<IP_VM>:2358

curl -s $J0/languages | jq '.[] | select(.name | test("Python|C\\+\\+|Java|^C "))'
```

Ghi lại `language_id` của các ngôn ngữ sẽ hỗ trợ. Với bản 1.13.1 thường là:
Python 3 = `71`, C++ = `54`, Java = `62`, C = `50`. **Hãy kiểm tra lại bằng lệnh trên**,
đừng hard-code theo tài liệu này.

---

## Bước 6: Thử đủ 5 loại kết quả

Dùng `wait=true` để nhận kết quả ngay (chỉ dùng khi thử; khi làm thật thì bỏ `wait` và poll bằng token).

```bash
submit() {  # $1 = JSON body
  curl -s -X POST "$J0/submissions?base64_encoded=false&wait=true" \
    -H 'Content-Type: application/json' -d "$1" \
    | jq '{status: .status.description, stdout, stderr, compile_output, time, memory}'
}
```

**1. Accepted (Python):**
```bash
submit '{"language_id":71,"source_code":"print(int(input())*2)","stdin":"21","expected_output":"42"}'
```

**2. Wrong Answer:**
```bash
submit '{"language_id":71,"source_code":"print(int(input())+1)","stdin":"21","expected_output":"42"}'
```

**3. Time Limit Exceeded (C++):**
```bash
submit '{"language_id":54,"source_code":"int main(){while(true){}}","cpu_time_limit":1}'
```

**4. Compile Error (C++):** bài này **phải gọi với `base64_encoded=true`**. Thông báo lỗi của GCC có
dấu nháy ‘ ’, nên nếu gọi với `base64_encoded=false` thì Judge0 không trả kết quả mà chỉ trả về
`{"error":"some attributes for this submission cannot be converted to UTF-8, use base64_encoded=true ..."}`.

```bash
SRC=$(printf 'int main(){ return 0 }' | base64 -w0)
R=$(curl -s -X POST "$J0/submissions?base64_encoded=true&wait=true" \
  -H 'Content-Type: application/json' -d "{\"language_id\":54,\"source_code\":\"$SRC\"}")
echo "$R" | jq '.status'                          # {"id":6,"description":"Compilation Error"}
echo "$R" | jq -r '.compile_output' | base64 -d   # nội dung lỗi biên dịch
```

> ⚠️ **Quy ước cho backend (`judge_client`)**: **luôn gửi và nhận bằng `base64_encoded=true`**.
> Code, stdin và output của sinh viên có thể chứa ký tự bất kỳ. Lưu ý: base64 Judge0 trả về
> có ký tự xuống dòng giữa chuỗi, nên khi giải mã phải bỏ `\n` trước, hoặc dùng
> `base64.b64decode` của Python (hàm này tự bỏ qua ký tự xuống dòng).

**5. Runtime Error (Python):**
```bash
submit '{"language_id":71,"source_code":"print(1/0)"}'
```

Bảng status id cần nhớ khi code phần `judge_client`:

| id | Ý nghĩa |
|---|---|
| 1, 2 | In Queue, Processing (chưa có kết quả, cần poll tiếp) |
| 3 | Accepted |
| 4 | Wrong Answer |
| 5 | Time Limit Exceeded |
| 6 | Compilation Error |
| 7–12 | Runtime Error (SIGSEGV, SIGXFSZ, SIGFPE, SIGABRT, NZEC, Other) |
| 13 | Internal Error (lỗi của Judge0, không phải lỗi của sinh viên) |
| 14 | Exec Format Error |

Kết quả đo thử trên VM (4 CPU, 4GB, Judge0 CE 1.13.1, ngày 29/09/2026):

| Bài | Kết quả | time | memory |
|---|---|---|---|
| Python AC | Accepted | 0.008s | ~4 MB |
| C++ AC (đọc stdin) | Accepted | 0.001s | ~6.7 MB |
| Java AC | Accepted | 0.027s | ~50 MB |
| C++ vòng lặp vô hạn, `cpu_time_limit=1` | Time Limit Exceeded | 1.096s | ~28 MB |

Java tốn RAM hơn hẳn (JVM), nên đặt `memory_limit` cho Java cao hơn các ngôn ngữ khác.

## Bước 7: Thử batch (giống cách backend sẽ chấm nhiều testcase)

```bash
curl -s -X POST "$J0/submissions/batch?base64_encoded=false" \
  -H 'Content-Type: application/json' -d '{"submissions":[
    {"language_id":71,"source_code":"print(int(input())*2)","stdin":"1","expected_output":"2"},
    {"language_id":71,"source_code":"print(int(input())*2)","stdin":"5","expected_output":"10"},
    {"language_id":71,"source_code":"print(int(input())*2)","stdin":"7","expected_output":"15"}
  ]}' | tee /tmp/batch.json

TOKENS=$(jq -r 'map(.token) | join(",")' /tmp/batch.json)
curl -s "$J0/submissions/batch?tokens=$TOKENS&base64_encoded=false&fields=token,status" | jq
```

Kết quả mong đợi: 2 testcase đầu ra `Accepted`, testcase thứ 3 ra `Wrong Answer`.
Backend sẽ tổng hợp như sau: `passed_count = 2`, và `status` của Submission lấy theo testcase đầu tiên bị fail.

---

## Xong spike khi

- [ ] Bước 6 ra đúng cả 5 loại kết quả
- [ ] Bước 7 batch chạy được và poll ra kết quả bằng token
- [ ] Đã ghi `language_id` thật và `JUDGE0_URL` để báo cho nhóm
- [ ] Đã đo thử: một bài Python đơn giản chạy mất bao lâu (`time`), bao nhiêu RAM (`memory`)

## Xử lý sự cố

| Triệu chứng | Nguyên nhân / cách xử lý |
|---|---|
| Mọi bài đều ra `Internal Error` (status 13), log có `No such file or directory @ rb_sysopen - /box/...` | Máy vẫn đang ở cgroup v2. Chạy lại `stat -fc %T /sys/fs/cgroup/` và làm lại bước 2 |
| `workers` cứ restart liên tục | Xem `docker compose logs workers`. Thường do thiếu `REDIS_PASSWORD`/`POSTGRES_PASSWORD` hoặc DB chưa sẵn sàng. Chạy `docker compose restart` |
| Java luôn báo lỗi bộ nhớ hoặc Runtime Error | JVM cần nhiều RAM. Tăng `memory_limit` (đơn vị KB, vd `256000`) |
| Máy thật không `curl` được tới VM | Kiểm tra IP bằng `multipass info judge0`, firewall (`ufw`) trong VM |

## Lưu ý bảo mật

- Container của Judge0 chạy ở chế độ `privileged`. **Không public cổng 2358 ra internet**, chỉ cho backend gọi tới.
- Khi chia sẻ cho nhóm hoặc lên server thật, **bắt buộc bật `AUTHN_TOKEN`** trong `judge0.conf` (xem bước A2). Backend gửi token này qua header `X-Auth-Token`.
- CI trên GitHub không chạy được Judge0 (không có cgroup v1), nên test backend phải **mock** `judge_client`.

## Chia sẻ Judge0 cho cả nhóm (Tailscale)

Cả nhóm dùng chung **1 Judge0** do một người host (gọi là **người host**). Các thành viên khác
**không cài Judge0**, chỉ cần cài Tailscale để kết nối tới máy của người host.

```
Máy thành viên ──(Tailscale, mã hoá)──▶ VM judge0 (100.x.y.z:2358) trên máy người host
```

**Vì sao dùng Tailscale:**
- Dùng được dù mọi người ở khác mạng (nhà, trường, 4G). Không cần mở cổng router.
- Judge0 **không bị lộ ra internet**, chỉ người được chia sẻ mới kết nối được.
- VM của Multipass chỉ gọi được từ chính máy người host, nên cài Tailscale **thẳng trong VM** để VM có IP riêng mà thành viên gọi tới được.

**Ai cần kết nối và khi nào:** FE gần như không cần, vì FE gọi backend chứ không gọi Judge0.
BE chỉ cần kết nối khi làm phần chấm bài (`judge_client`, Phase 3), vì unit test đã mock Judge0.

### Phần A: Người host (làm 1 lần)

Điều kiện: đã làm xong Bước 1–7 ở trên, Judge0 chạy ổn trong VM.

**A1. Cài Tailscale trong VM** (chạy trong `multipass shell judge0`, từng lệnh một):

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

```bash
sudo tailscale up --hostname judge0
```

Lệnh thứ hai in ra một link đăng nhập. Mở link trên trình duyệt, đăng nhập bằng tài khoản
Tailscale của người host (tạo mới bằng Google/GitHub/Microsoft đều được). Sau đó lấy IP của VM:

```bash
tailscale ip -4        # vd 100.101.102.103, đây là IP gửi cho nhóm
```

Tailscale tự khởi động cùng VM, nên sau khi VM khởi động lại không phải chạy `tailscale up` nữa.

**A2. Bật xác thực bằng token cho Judge0** (trong thư mục `judge0-v1.13.1`):

```bash
sed -i "s/^AUTHN_TOKEN=.*/AUTHN_TOKEN=$(openssl rand -hex 24)/" judge0.conf
grep -E '^AUTHN_(HEADER|TOKEN)=' judge0.conf     # AUTHN_HEADER để trống = dùng mặc định X-Auth-Token
```

```bash
docker compose restart server workers
```

Kiểm tra: gọi **không có token** thì phải bị từ chối (mã 401), gọi **có token** thì được chấm (mã 201):

> Dán **từng khối một**. Dán nhiều dòng cùng lúc dễ bị dính dòng, vd `TOKEN=...` dính với
> `BODY=...` làm token bị sai, và mọi lệnh đều ra 401.

```bash
TOKEN=$(grep '^AUTHN_TOKEN=' judge0.conf | cut -d= -f2)
```

```bash
BODY='{"language_id":71,"source_code":"print(1)"}'
```

```bash
# Không có token: phải ra 401
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:2358/submissions -H 'Content-Type: application/json' -d "$BODY"
```

```bash
# Token sai: phải ra 401
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:2358/submissions -H 'Content-Type: application/json' -H 'X-Auth-Token: sai-token' -d "$BODY"
```

```bash
# Có token: phải ra 201
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:2358/submissions -H 'Content-Type: application/json' -H "X-Auth-Token: $TOKEN" -d "$BODY"
```

**A3. Chia sẻ máy `judge0` cho từng thành viên:**

1. Vào https://login.tailscale.com/admin/machines
2. Ở dòng máy `judge0`, bấm **`...`** → **Share...**
3. Nhập email của thành viên (hoặc tạo link mời) rồi gửi đi

Chia sẻ theo cách này thì thành viên **chỉ thấy đúng máy `judge0`**, không thấy các thiết bị khác
của người host. Họ dùng tailnet (mạng Tailscale riêng) của chính họ, nên không phải vào chung
tailnet của người host. Giới hạn của gói miễn phí có thể thay đổi, xem trang giá của Tailscale.

**A4. Gửi cho thành viên** qua tin nhắn riêng, **không commit lên git**:
- IP Tailscale của VM (`100.x.y.z`)
- `AUTHN_TOKEN`

**Vận hành hằng ngày:**
- Thành viên chỉ gọi được Judge0 khi **máy người host đang bật và VM đang chạy**. Sau khi khởi
  động lại máy, chạy `multipass start judge0`. Các container Judge0 và Tailscale sẽ tự chạy lại.
- Muốn **thu hồi quyền** của một người: vào trang Machines → `judge0` → Share → gỡ người đó.
- Muốn **đổi token** (vd khi token bị lộ): làm lại bước A2 rồi gửi token mới cho nhóm.

### Phần B: Thành viên (mỗi người làm 1 lần)

**B1. Cài Tailscale** và đăng nhập bằng tài khoản của mình:
- Windows / macOS: tải app tại https://tailscale.com/download, đăng nhập.
- Linux: `curl -fsSL https://tailscale.com/install.sh | sh` rồi `sudo tailscale up`.

**B2. Nhận chia sẻ:** mở email hoặc link mời từ người host, bấm **Accept**. Máy `judge0` sẽ xuất hiện
trong danh sách máy của mình trên Tailscale.

**B3. Kiểm tra kết nối** (thay IP và token bằng thông tin người host gửi):

```bash
# Linux / macOS / Git Bash
curl -s -H "X-Auth-Token: <TOKEN>" http://100.x.y.z:2358/about
```

```powershell
# Windows PowerShell: phải gõ curl.exe, vì curl trong PowerShell là lệnh khác
curl.exe -s -H "X-Auth-Token: <TOKEN>" http://100.x.y.z:2358/about
```

Kết quả đúng là một đoạn JSON có `"version":"1.13.1"`.

**B4. Dùng trong backend (từ Phase 3):** khai báo trong file `.env` ở máy mình (không commit):

```env
JUDGE0_URL=http://100.x.y.z:2358
JUDGE0_AUTH_TOKEN=<TOKEN>
```

Tên biến sẽ được chốt khi viết `judge_client`, lúc đó cập nhật cả `.env.example`.

### Xử lý sự cố khi kết nối

| Triệu chứng | Cách xử lý |
|---|---|
| `curl` bị treo rồi timeout | Máy người host đang tắt hoặc VM chưa chạy (`multipass start judge0`). Kiểm tra Tailscale đã bật ở cả 2 phía: `tailscale status` phải thấy máy `judge0` |
| Không thấy máy `judge0` trong Tailscale | Chưa bấm Accept lời mời chia sẻ, hoặc đang đăng nhập Tailscale bằng tài khoản khác với email được mời |
| Trả về 401 | Sai hoặc thiếu header `X-Auth-Token`, hoặc người host vừa đổi token |
| `tailscale ping judge0` được nhưng `curl` không được | Container Judge0 chưa chạy. Người host chạy `docker compose ps` trong VM để kiểm tra |

---

## Phụ lục: chuyển máy thật sang cgroup v1

**Chỉ áp dụng khi systemd ≤ 255.** Nếu systemd 256–257 thì phải thêm cả
`SYSTEMD_CGROUP_ENABLE_LEGACY_FORCE=1`. Nếu systemd ≥ 258 thì **không làm được**, phải dùng VM.

```bash
sudo sed -i 's/^GRUB_CMDLINE_LINUX="\(.*\)"/GRUB_CMDLINE_LINUX="\1 systemd.unified_cgroup_hierarchy=0"/' /etc/default/grub
sudo update-grub && sudo reboot
```

Muốn hoàn tác thì xoá tham số vừa thêm trong `/etc/default/grub`, rồi chạy lại `update-grub` và reboot.
