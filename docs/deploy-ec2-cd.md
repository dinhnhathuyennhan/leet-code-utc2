# Quy trình nhánh, phát hành và triển khai (GitFlow + CI/CD)

Tài liệu này dành cho cả nhóm. Nó trả lời các câu hỏi:
- Code đi từ máy mình lên production như thế nào?
- Nhánh nào dùng để làm gì?
- Đặt version ra sao?
- Làm gì để deploy, và làm gì để rollback?

Đọc nhanh: **mục 1–6** là việc hằng ngày của mọi thành viên. **Mục 7–9** dành cho người phụ trách deploy. **Mục 10** là danh sách cấu hình cần **chủ repo** thực hiện.

---

## 1. Tổng quan

```
feature/* ──PR──► develop ──tách──► release/X.Y.Z ──push──► CD ──duyệt──► EC2 production
                     ▲                    │
                     │                    └──PR──► main ──tag vX.Y.Z (đánh dấu bản đã phát hành)
                     └────── merge ngược (back-merge) ───────┘
```

| Thành phần | Vai trò |
|---|---|
| **CI** (`.github/workflows/ci.yaml`) | Chạy `ruff`, `pytest`, lint, `tsc`, vitest, `next build`. Kích hoạt khi có PR vào `develop`/`main`, khi push vào `develop`/`main`, và khi CD gọi lại |
| **CD** (`.github/workflows/cd.yaml`) | **Chỉ** chạy khi push nhánh `release/**`, hoặc khi chạy tay để rollback. Các bước: gọi lại CI, build và push image, **chờ người duyệt**, deploy lên EC2 |
| **`deploy/ssh-deploy.sh`** | Cửa vào duy nhất của key SSH mà CD dùng: chỉ nhận lệnh `deploy <version> <sha>`, tải file deploy của đúng commit rồi gọi `deploy.sh` |
| **`deploy/deploy.sh`** | Chạy trên EC2: backup DB, đổi version, chạy container, kiểm tra sức khoẻ hệ thống, tự rollback khi lỗi |

Đây là **Continuous Delivery**: mỗi lần release, image luôn được build sẵn, nhưng **phải có người duyệt** thì mới lên production.

---

## 2. Các nhánh

| Nhánh | Tách từ | Merge vào | Ai tạo | CI | CD | Ghi chú |
|---|---|---|---|---|---|---|
| `main` | — | — | — | ✅ | ❌ | Luôn trùng với bản **đang chạy trên production**. Không push thẳng |
| `develop` | `main` (một lần) | — | — | ✅ | ❌ | Nơi gộp code của các tính năng đã xong. Không push thẳng |
| `feature/<tên>` | `develop` | `develop` (qua PR) | Mọi thành viên | ✅ (ở PR) | ❌ | Tính năng mới, ví dụ `feature/create-admin-tool` |
| `fix/<tên>`, `bugfix/<tên>` | `develop` | `develop` (qua PR) | Mọi thành viên | ✅ (ở PR) | ❌ | Sửa lỗi **chưa** lên production |
| `release/X.Y.Z` | **`develop`** | `main` **và** `develop` | Người phụ trách release | ✅ (CD gọi) | ✅ | Push lên nhánh này là **kích hoạt deploy** |
| `release/X.Y.Z` (bản vá) | **`main`** | `main` **và** `develop` | Người phụ trách release | ✅ (CD gọi) | ✅ | Sửa gấp lỗi trên production, xem mục 6 |

Tên nhánh viết thường, các từ nối bằng `-`. Commit theo Conventional Commits: `feat(problems): ...`, `fix(lessons): ...`, `chore(deploy): ...`, `docs(...)`, `test(...)`.

---

## 3. Đặt version

Theo **Semantic Versioning** `MAJOR.MINOR.PATCH`:

| Tăng | Khi nào | Ví dụ |
|---|---|---|
| **PATCH** | Chỉ sửa lỗi, không đổi API, không thêm tính năng | `1.0.0` → `1.0.1` |
| **MINOR** | Thêm tính năng mà vẫn tương thích ngược (thường là xong một phase) | `1.0.1` → `1.1.0` |
| **MAJOR** | Thay đổi không tương thích ngược: đổi hoặc xoá API mà FE cũ đang dùng, migration không quay lại được | `1.4.2` → `2.0.0` |
| Pre-release | Bản thử, nếu cần: `-rc.1`, `-rc.2` | `1.1.0-rc.1` |

Quy tắc bắt buộc:
- **Tên nhánh chính là version.** `release/1.2.0` sinh ra 2 image `chamcode-backend:1.2.0` và `chamcode-frontend:1.2.0` (kèm tag `sha-<commit>`). Không có tag `latest`.
- **Version đã phát hành thì bất biến.** Khi `release/1.2.0` đã build xong, pipeline sẽ từ chối build lại `1.2.0`. Cần sửa thì tạo version mới (`1.2.1`).
- Sau khi deploy thành công, gắn **git tag `vX.Y.Z`** lên commit merge vào `main` (mục 5, bước 6). Nhìn tag là biết production từng chạy những bản nào.
- Bản phát hành đầu tiên qua CD là **`1.0.0`**. Các bản `0.9.x` trước đó được build và deploy bằng tay.

---

## 4. Làm tính năng hằng ngày (mọi thành viên)

```bash
git checkout develop && git pull
git checkout -b feature/ten-tinh-nang
# ... code, commit ...
git push -u origin feature/ten-tinh-nang
```
1. Mở **PR vào `develop`**. CI tự chạy.
2. Đợi CI xanh và **ít nhất 1 người review** rồi mới merge. Nên dùng **Squash and merge** cho gọn lịch sử.
3. Xoá nhánh sau khi merge.

Không merge khi CI đỏ. Không push thẳng lên `develop` hoặc `main`.

---

## 5. Phát hành một version (người phụ trách release)

Ví dụ phát hành `1.1.0`.

**Bước 1: chuẩn bị.** `develop` có CI xanh. Các tính năng định đưa vào bản này đã merge xong.

**Bước 2: tạo nhánh release từ `develop` và push.** Lần push này kích hoạt CD.
```bash
git checkout develop && git pull
git checkout -b release/1.1.0
git push -u origin release/1.1.0
```

**Bước 3: theo dõi** ở Actions → **CD** → run của `release/1.1.0`:
1. **CI**: chạy lại toàn bộ test trên đúng commit này.
2. **Xác định version**: kiểm tra tên nhánh và cấu hình, đồng thời chặn trường hợp version đã có.
3. **Build & push** backend và frontend lên Docker Hub.
4. **Deploy**: dừng ở trạng thái *Waiting*, chờ người duyệt.

**Bước 4: duyệt.** Một người trong danh sách reviewer của environment `production` bấm **Review deployments** → tick `production` → **Approve and deploy**.
- Nên duyệt vào lúc ít người dùng.
- Bấm **Reject** thì không deploy. Image vẫn nằm trên Docker Hub và có thể deploy sau bằng cách chạy tay (mục 7).

**Bước 5: kiểm tra.**
- Job Deploy in log của server trong nhóm *Output trên server*, rồi chạy smoke test.
- Mở web, đăng nhập, nộp thử một bài.

**Bước 6: đóng release** (bắt buộc, để `main` và `develop` khớp với production):
1. Mở **PR `release/1.1.0` → `main`**, merge bằng **Create a merge commit**. Không dùng squash, để giữ chung lịch sử với `develop`.
2. Gắn tag lên commit vừa merge vào `main`:
   ```bash
   git checkout main && git pull
   git tag -a v1.1.0 -m "Release 1.1.0"
   git push origin v1.1.0
   ```
   Hoặc dùng GitHub → Releases → *Draft a new release* → tag `v1.1.0`, target `main` → *Generate release notes*.
3. Mở **PR `main` → `develop`** (back-merge) nếu nhánh release có commit mới so với `develop`, ví dụ khi có sửa lỗi trong lúc release.
4. Xoá nhánh `release/1.1.0`.

Tag `v*` **không kích hoạt** CD. Nó chỉ đánh dấu lịch sử.

**Nếu phát hiện lỗi giữa chừng:**
- CI đỏ: chưa có image nào được push. Sửa ngay trên `release/1.1.0` rồi push lại; CD tự chạy lại.
- Image đã build xong (dù đã deploy hay chưa): **không push sửa vào `release/1.1.0` nữa**, vì pipeline sẽ báo version đã phát hành. Merge bản sửa vào `develop` rồi tạo `release/1.1.1`.

---

## 6. Vá gấp lỗi trên production (hotfix)

Dùng khi production đang lỗi mà `develop` đã có tính năng mới chưa muốn phát hành.

```bash
git checkout main && git pull
git checkout -b release/1.1.1          # tăng PATCH, tách từ main (không phải develop)
# ... sửa lỗi, commit ...
git push -u origin release/1.1.1       # CD chạy -> duyệt -> deploy
```
Sau đó làm **bước 6 của mục 5**: PR vào `main`, gắn tag `v1.1.1`, **back-merge vào `develop`**. Nếu quên back-merge, lỗi sẽ quay lại ở bản release sau.

---

## 7. Rollback và deploy lại

**Tự động:** nếu bản mới không healthy trong 240 giây, frontend không trả lời, hoặc API public không trả lời, `deploy.sh` tự đưa về version trước. Job Deploy báo đỏ, log in kèm 60 dòng log backend.
- Nếu bản lỗi **đã chạy migration**, image cũ sẽ không khởi động được với schema mới. Vì vậy `deploy.sh` **khôi phục DB từ bản backup vừa tạo** trước khi chạy image cũ. DB lỗi được giữ lại với tên `ChamCodeDB_failed_<thời gian>` để điều tra; xoá tay khi không cần (`DROP DATABASE`). Dữ liệu ghi trong vài phút bản lỗi chạy chỉ còn trong DB đó.
- Job báo **"ĐÃ quay về version trước"** nghĩa là backend cũ đã healthy trở lại. Job báo **"rollback cũng thất bại"** nghĩa là production có thể đang down: SSH vào server xử lý ngay.

**Rollback bằng tay:** Actions → **CD** → **Run workflow**:
- **Use workflow from**: chọn nhánh release của version muốn quay về, ví dụ `release/1.0.0`. Nhánh đó đã bị xoá thì chọn **tag** `v1.0.0`; khi đó environment `production` phải cho phép cả tag `v*` (xem mục 10.3).
- **version**: `1.0.0`.
- Duyệt như mục 5, bước 4.

Khi chạy tay, pipeline **không build**. Nó chỉ kiểm tra image `1.0.0` còn trên Docker Hub rồi deploy.

Version chọn ở ô **version** phải khớp với nhánh/tag ở ô **Use workflow from** (ví dụ `1.0.0` với `release/1.0.0` hoặc `v1.0.0`). Server từ chối commit không phải đầu nhánh `release/<version>` hoặc tag `v<version>`.

**Rollback bằng tay qua một migration thì phải restore DB trước.** Ví dụ đang chạy `1.1.0` (có migration mới), muốn về `1.0.0`: image `1.0.0` không chạy được với schema của `1.1.0`, nên lần deploy đó sẽ lỗi rồi tự quay lại `1.1.0`. Muốn về thật thì làm trên server:
```bash
cd /opt/chamcode
ls -1t ~/backups/before-1.1.0-*.dump | head -1     # backup tạo ngay trước khi lên 1.1.0
docker compose stop backend
docker compose exec -T postgres pg_restore -U chamcode -d ChamCodeDB --clean --if-exists --no-owner < <file vừa tìm>
bash deploy.sh 1.0.0
```
Dữ liệu ghi sau thời điểm backup đó sẽ mất. Backup nằm ở `/home/ubuntu/backups` trên EC2, giữ 10 bản gần nhất.

**Khi GitHub hoặc AWS gặp sự cố**, chạy thẳng trên server, kết quả giống hệt pipeline:
```bash
cd /opt/chamcode && bash deploy.sh 1.0.0
```

---

## 8. Hạ tầng production

- **EC2 `chamcode-app`** (t3.micro, Ubuntu 24.04): `/opt/chamcode` chạy postgres, backend, frontend và caddy theo `deploy/docker-compose.prod.yml`. File `.env` chỉ nằm trên server, không bao giờ commit.
- **EC2 Judge0**: cùng VPC, backend gọi qua private IP.
- **Docker Hub**: `<user>/chamcode-backend`, `<user>/chamcode-frontend`.
- Mỗi lần deploy, server tải `docker-compose.prod.yml`, `Caddyfile`, `deploy.sh` của **đúng commit đang release** từ repo. Muốn đổi cấu hình server thì sửa các file đó qua PR như code bình thường.
- Riêng `ssh-deploy.sh` **không** được tự cập nhật, vì nó là chốt chặn của key deploy. Sửa file này thì phải copy tay lên server (mục 9.2b).
- CD deploy qua **SSH**, không qua AWS SSM: tài khoản AWS đang ở Free Plan, không bật được IAM Identity provider (OIDC) nếu không upgrade.
- Instance chỉ **start khi làm việc hoặc demo**. Trước khi bấm duyệt deploy, phải chắc chamcode-app đang chạy.

---

## 9. Cấu hình một lần (người phụ trách deploy)

### 9.1 Docker Hub
1. Account settings → Personal access tokens → tạo token `github-actions`, quyền **Read & Write**. Đưa token này cho chủ repo để nhập vào secret của environment `release-build` (mục 10.3).
2. Nếu repo image để private: trên EC2, đăng nhập một lần bằng user `ubuntu`: `docker login -u <user>`, dùng token Read-only.

### 9.2 Key SSH cho GitHub Actions

GitHub Actions SSH vào chamcode-app bằng một **key riêng, chỉ dùng cho deploy**. Trên server, key này bị khoá bằng *forced command*: dù gửi lệnh gì, server cũng chỉ chạy `ssh-deploy.sh`. Script đó:
- chỉ nhận lệnh `deploy <version> <sha>`;
- hỏi GitHub (`git ls-remote`) và chỉ chấp nhận `<sha>` là **đầu nhánh `release/<version>` hoặc commit của tag `v<version>`**. Commit của nhánh feature, fork hay PR đều bị từ chối.

Lộ key thì kẻ xấu cũng không có shell và chỉ deploy lại được bản đã nằm trên nhánh release hoặc tag. Ai có quyền push `release/*` vẫn đưa được code lên production, nên vẫn cần ruleset ở mục 10.2 và giữ key trong environment `production` (mục 10.3).

**a. Tạo key (máy local, ngoài thư mục repo):**
```bash
ssh-keygen -t ed25519 -C github-cd-chamcode -f github-cd-chamcode
```
Nhấn Enter 2 lần để **không đặt passphrase** (GitHub Actions không nhập passphrase được). Kết quả là 2 file:
- `github-cd-chamcode`: private key. Dán **toàn bộ nội dung** (kể cả dòng `BEGIN`/`END`) vào secret `EC2_SSH_KEY` của **environment `production`** (mục 10.3), sau đó **xoá file này** khỏi máy. Repo cá nhân thì chỉ chủ repo tạo được environment secret: gửi key cho chủ repo qua kênh riêng.
- `github-cd-chamcode.pub`: public key, dùng ở bước b.

**b. Cài trên server** (SSH vào bằng key cá nhân như bình thường, user `ubuntu`):
```bash
# Lấy ssh-deploy.sh từ develop (sau khi PR chứa file này đã merge)
curl -fsSL https://raw.githubusercontent.com/dinhnhathuyennhan/leet-code-utc2/develop/deploy/ssh-deploy.sh -o /opt/chamcode/ssh-deploy.sh
sed -i 's/\r$//' /opt/chamcode/ssh-deploy.sh
chmod 755 /opt/chamcode/ssh-deploy.sh

# Thêm 1 dòng vào authorized_keys (KHÔNG xoá dòng key cá nhân đang có)
echo 'restrict,command="/opt/chamcode/ssh-deploy.sh" <dán nội dung file github-cd-chamcode.pub>' >> ~/.ssh/authorized_keys
```

Thử từ máy local, trước khi xoá private key:
```bash
ssh -i github-cd-chamcode ubuntu@<ELASTIC_IP> "ls"
```
Kết quả đúng là bị từ chối với dòng `ssh-deploy: chỉ cho phép lệnh: deploy <version> <commit-sha>`. Như vậy key vào được nhưng không có shell.

Thử tiếp với một commit **không** nằm trên nhánh release (ví dụ đầu nhánh `develop`, lấy bằng `git rev-parse origin/develop`):
```bash
ssh -i github-cd-chamcode ubuntu@<ELASTIC_IP> "deploy 0.9.0 <sha-của-develop>"
```
Kết quả đúng: `ssh-deploy: commit ... không phải đầu nhánh release/0.9.0 hoặc tag v0.9.0`. Không có gì trên server bị thay đổi.

**c. Host key của server** (để GitHub biết đúng server, chống giả mạo). Trên server:
```bash
cat /etc/ssh/ssh_host_ed25519_key.pub
```
Đặt variable `EC2_KNOWN_HOSTS` = `<ELASTIC_IP> ` + nội dung vừa in, ví dụ `13.250.1.2 ssh-ed25519 AAAAC3Nza...`.

**d. Security Group của chamcode-app:** inbound **SSH 22 từ `0.0.0.0/0`**, vì máy chạy GitHub Actions không có IP cố định. Bù lại:
- Server chỉ cho đăng nhập bằng key. Kiểm tra: `sudo sshd -T | grep -i passwordauthentication` phải ra `no` (mặc định của Ubuntu AMI).
- Nên cài `fail2ban` để chặn IP dò mật khẩu: `sudo apt install -y fail2ban`. Jail `sshd` tự bật trên Ubuntu.
- Instance chỉ chạy khi cần (làm việc, demo), nên thời gian mở ra internet ngắn.

**e. Elastic IP bắt buộc:** IP không đổi khi stop/start. Nếu đổi IP, phải sửa cả `EC2_HOST` và `EC2_KNOWN_HOSTS`.

### 9.3 Trên EC2
`/opt/chamcode/.env` phải có sẵn, theo mẫu `deploy/.env.prod.example`. Pipeline chỉ sửa 2 dòng `BACKEND_TAG` và `FRONTEND_TAG`.

Biến môi trường mới từ bản sau `1.0.0-rc.1`. Thêm tay vào `/opt/chamcode/.env` trước khi deploy, vì `deploy.sh` không tự thêm:

| Biến | Giá trị production | Ý nghĩa |
|---|---|---|
| `API_DOCS_ENABLED` | `false` | Ẩn Swagger `/docs`, `/redoc`, `/openapi.json` |
| `GRADING_CHUNK_SIZE` | `10` | Chấm theo lô, dừng sớm sau test quá thời gian |

Đồng thời xoá `"go":{...}` khỏi `JUDGE_LANGUAGES`, vì Go đã bị loại bỏ. Nếu để sót, backend chỉ ghi cảnh báo và bỏ qua.

`Caddyfile` đã thêm header bảo mật (HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`) và bỏ header `Server`. Sau lần deploy đầu tiên có thay đổi này, kiểm tra cấu hình bằng:

```bash
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

```bash
curl -sI https://<API_DOMAIN>/ | grep -i -E "strict-transport|x-frame|server"
```

---

## 10. Cấu hình cần CHỦ REPO thực hiện

Các mục sau cần quyền **Admin** của repo. Repo đang **public**, nên Rulesets và Environment protection đều dùng được với gói miễn phí.

### 10.1 Quyền thành viên

Repo hiện thuộc **tài khoản cá nhân**. Với repo cá nhân, mọi collaborator có quyền như nhau (ghi), chỉ chủ repo là admin. **Không có** các role trung gian như *Maintain*. Hệ quả:
- Ruleset **không phân biệt được** "người phụ trách release" với các thành viên khác. Bypass list chỉ chọn được *Repository admin*, tức là chủ repo.
- Chỉ chủ repo mới quản lý được secrets, variables và environments.

Có 2 hướng:

| Hướng | Cách làm | Kết quả |
|---|---|---|
| **A. Giữ repo cá nhân** (đơn giản) | Chủ repo tự làm mục 10.2–10.5 | Ai cũng tạo được nhánh `release/*`, nên ai cũng kích hoạt được build. Nhưng **deploy vẫn phải được duyệt** bởi reviewer của environment `production` (mục 10.3). Đây là chốt chặn chính |
| **B. Chuyển repo vào GitHub Organization** (khuyến nghị nếu muốn chặt) | Tạo Organization miễn phí → Settings của repo → *Transfer ownership* → mời thành viên. Gán role **Maintain** cho người phụ trách release, **Write** cho các thành viên khác | Bypass list của ruleset chọn được role/team, nên chỉ người phụ trách mới tạo được `release/*` và tag `v*`. Remote cũ vẫn tự chuyển hướng sang địa chỉ mới |

Dù chọn hướng nào, **danh sách Required reviewers ở mục 10.3** vẫn chọn được từng người cụ thể.

### 10.2 Rulesets (Settings → Rules → Rulesets → New ruleset)

**Ruleset 1: `protect-main`** (New branch ruleset)
- Enforcement status: **Active**
- Target branches: `main`
- Bypass list: chỉ **Repository admin**, chế độ *For pull requests only*. Dùng khi có sự cố khẩn cấp.
- Bật các rule:
  - ☑ Restrict deletions
  - ☑ Block force pushes
  - ☑ Require linear history: **không** bật, vì release và back-merge dùng merge commit.
  - ☑ Require a pull request before merging
    - Required approvals: **1**
    - ☑ Dismiss stale pull request approvals when new commits are pushed
    - ☑ Require conversation resolution before merging
  - ☑ Require status checks to pass
    - Thêm 2 check: **`backend`** và **`frontend`** (tên 2 job trong `ci.yaml`). Ô chọn chỉ gợi ý tên check đã từng chạy, nên cần CI chạy ít nhất một lần trước đó.

**Ruleset 2: `protect-develop`**
- Target branches: `develop`
- Các rule giống `protect-main`: Restrict deletions, Block force pushes, Require PR (1 approval), Require status checks `backend` và `frontend`.

**Ruleset 3: `release-branches`**
- Target branches: pattern `release/**`
- ☑ Block force pushes: version đã build không bị viết lại lịch sử.
- ☐ Restrict deletions: để **tắt**, vì cần xoá nhánh release sau khi đóng.
- ☑ **Restrict creations**: **chỉ bật nếu đi theo hướng B** (Organization). Bypass list chọn role **Maintain**, để chỉ người phụ trách release mới tạo được nhánh `release/*`. Với hướng A, bật rule này thì chỉ mình chủ repo tạo được release.

**Ruleset 4: `release-tags`** (New **tag** ruleset)
- Target tags: pattern `v*`
- ☑ Restrict updates, ☑ Restrict deletions, ☑ Block force pushes: tag đã gắn cho một version thì không bị dời hoặc xoá.
- ☑ Restrict creations: chỉ bật theo hướng B, bypass role **Maintain**. Lý do giống ruleset 3.

### 10.3 Environments (Settings → Environments → New environment)

**Vì sao secret phải nằm trong environment, không ở cấp repo:** secret cấp repo thì workflow của **mọi nhánh** đều đọc được. Một thành viên chỉ cần push nhánh `feature/x` kèm một workflow tự viết là lấy được key SSH hoặc token Docker Hub, rồi deploy hoặc ghi đè image mà không qua ai duyệt. Secret trong environment chỉ được cấp cho job khai báo đúng environment đó, và chỉ khi chạy từ nhánh/tag được cho phép.

**Environment 1: `release-build`** (job *Xác định version* và *Build & push* dùng)
- Không cần reviewer.
- **Deployment branches and tags** → *Selected branches and tags*: branch `release/*`, tag `v*`.
- **Environment secret** `DOCKERHUB_TOKEN`: token Read & Write ở mục 9.1.

**Environment 2: `production`** (job *Deploy* dùng)
- ☑ **Required reviewers**: thêm 1–2 người, ví dụ chủ repo và người phụ trách deploy.
- ☑ **Prevent self-review**: người kích hoạt release không tự duyệt được cho mình. Chỉ bật khi danh sách có từ 2 người trở lên.
- **Deployment branches and tags** → *Selected branches and tags*:
  - Branch pattern `release/*`
  - Tag pattern `v*` (để rollback được khi nhánh release đã bị xoá)
- **Environment secret** `EC2_SSH_KEY`: private key deploy ở mục 9.2a (toàn bộ nội dung file).

Nếu `DOCKERHUB_TOKEN` hoặc `EC2_SSH_KEY` đã lỡ tạo ở cấp repo thì **xoá bản cấp repo** sau khi tạo bản trong environment.

### 10.4 Variables của repo (Settings → Secrets and variables → Actions → tab Variables)

Các giá trị này không bí mật nên để ở cấp repo.

| Loại | Tên | Giá trị |
|---|---|---|
| Variable | `DOCKERHUB_USERNAME` | Username Docker Hub |
| Variable | `NEXT_PUBLIC_API_URL` | `https://<API_DOMAIN>`: có `https://`, không có `/` ở cuối |
| Variable | `APP_URL` | `https://<APP_DOMAIN>` |
| Variable | `EC2_HOST` | Elastic IP của chamcode-app |
| Variable | `EC2_KNOWN_HOSTS` | `<ELASTIC_IP> ssh-ed25519 AAAA...` (mục 9.2c) |
| Variable | `EC2_USER` | Tuỳ chọn, mặc định `ubuntu` |

### 10.5 Cài đặt chung (Settings → General và Settings → Actions)
- **Pull Requests**: bật *Allow merge commits* (dùng cho release và back-merge) và *Allow squash merging* (dùng cho feature). Bật **Automatically delete head branches**.
- **Actions → General → Workflow permissions**: chọn **Read repository contents and packages permissions**. Các workflow tự xin thêm quyền khi cần.
- **Actions → General → Fork pull request workflows**: *Require approval for first-time contributors*.

---

## 11. Lỗi thường gặp

| Triệu chứng | Nguyên nhân / cách xử lý |
|---|---|
| `Version ... đã được phát hành` | `release/X.Y.Z` đã build xong trước đó. Tạo nhánh với version mới |
| `Version '...' không đúng semver` | Tên nhánh sai, phải là `release/1.2.3` hoặc `release/1.2.3-rc.1` |
| `NEXT_PUBLIC_API_URL phải dạng https://...` | Sai variable của repo (mục 10.4) |
| Job Deploy không chờ duyệt mà chạy luôn | Environment `production` chưa bật Required reviewers |
| `Branch "release/..." is not allowed to deploy to production` | Thiếu pattern `release/*` (hoặc `v*`) ở mục 10.3 |
| `Không SSH được vào ...` + `Connection timed out` | Instance đang **stop**, hoặc Security Group chưa mở port 22 |
| `Host key verification failed` | `EC2_KNOWN_HOSTS` sai, hoặc Elastic IP đã đổi (mục 9.2c, 9.2e) |
| `Permission denied (publickey)` | `EC2_SSH_KEY` dán thiếu dòng, hoặc dòng trong `authorized_keys` sai (mục 9.2a–b) |
| `ssh-deploy: không tải được ... của commit` | Commit chưa có trên GitHub, hoặc repo đã chuyển sang private |
| `Server từ chối lệnh deploy` / `không phải đầu nhánh release/...` | Chạy tay với version không khớp nhánh/tag đã chọn; hoặc nhánh release vừa có commit mới đè lên commit đang deploy |
| `ssh-deploy: không hỏi được GitHub` | Server không ra được internet, hoặc thiếu `git` (`sudo apt-get install -y git`) |
| `Deploy ... thất bại. Server ĐÃ quay về version trước` | Đọc log `deploy.sh` ngay phía trên: pull lỗi (sai tag), backend không healthy, frontend hoặc API public không trả lời. Nếu bản lỗi đã migrate thì DB đã được khôi phục từ backup |
| `rollback cũng thất bại` | Production có thể đang down. SSH vào server: `cd /opt/chamcode && docker compose ps && docker compose logs --tail 100 backend`, xem mục 7 |
| Job `Xác định version` báo thiếu `DOCKERHUB_TOKEN` / login lỗi | Chưa tạo environment `release-build` hoặc secret chưa nằm trong đó (mục 10.3) |
| PR không merge được dù code đúng | CI chưa xanh, thiếu approval, hoặc còn comment chưa resolve |
