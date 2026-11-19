#!/usr/bin/env bash
# Deploy một version lên EC2 chamcode-app.
#
#   bash /opt/chamcode/deploy.sh <version>        ví dụ: bash deploy.sh 1.0.0
#
# Pipeline CD (.github/workflows/cd.yaml) gọi script này qua SSH (ssh-deploy.sh);
# chạy tay trên server cũng được (user ubuntu). Các bước:
#   1. kiểm tra version + .env, khoá để không có 2 lần deploy chạy song song
#   2. backup Postgres + ghi lại revision alembic trước khi đổi gì
#   3. ghi BACKEND_TAG/FRONTEND_TAG mới vào .env, pull image, up -d
#   4. chờ backend healthy + frontend trả lời + API public qua HTTPS
#   5. lỗi ở bước 3–4 => tự quay về tag cũ. Nếu bản lỗi đã chạy migration thì
#      khôi phục DB từ backup trước (code cũ không chạy được với schema mới).
#
# Mã thoát (cd.yaml dựa vào đây để báo lỗi):
#   0 thành công
#   1 lỗi trước khi đổi gì trên server
#   3 deploy lỗi, ĐÃ quay về version cũ và backend healthy
#   4 deploy lỗi VÀ rollback thất bại -> production có thể đang down, xử lý tay
#
# Script không in nội dung .env (repo public => log của GitHub Actions public).

set -Eeuo pipefail

VERSION="${1:-}"
APP_DIR="${APP_DIR:-/opt/chamcode}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
KEEP_BACKUPS="${KEEP_BACKUPS:-10}"
HEALTH_TIMEOUT_SECONDS="${HEALTH_TIMEOUT_SECONDS:-240}"
DB_NAME="ChamCodeDB"
DB_USER="chamcode"
EXIT_ROLLED_BACK=3
EXIT_ROLLBACK_FAILED=4

log() { printf '[deploy %s] %s\n' "$(date '+%F %T')" "$*"; }
die() { log "LỖI: $*"; exit 1; }

[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]] \
  || die "version không hợp lệ: '${VERSION}' (cần dạng 1.2.3 hoặc 1.2.3-rc.1)"

cd "$APP_DIR" || die "không có thư mục $APP_DIR"
[[ -f .env ]] || die "thiếu $APP_DIR/.env"
[[ -f docker-compose.prod.yml ]] || die "thiếu docker-compose.prod.yml"

# Chỉ một lần deploy tại một thời điểm (CD đã có concurrency, đây là lớp chặn khi chạy tay)
exec 9>/tmp/chamcode-deploy.lock
flock -n 9 || die "đang có một lần deploy khác chạy"

# File sửa trên Windows có thể mang CRLF -> giá trị biến dính '\r'
sed -i 's/\r$//' .env

env_value() { grep -E "^$1=" .env | tail -n1 | cut -d= -f2- || true; }
set_tag() {
  if grep -qE "^$1=" .env; then
    sed -i "s/^$1=.*/$1=$2/" .env
  else
    printf '%s=%s\n' "$1" "$2" >> .env
  fi
}

# psql_q "<sql>" [database]
psql_q() {
  docker compose exec -T postgres psql -U "$DB_USER" -d "${2:-$DB_NAME}" -v ON_ERROR_STOP=1 -qAtc "$1"
}
# Revision alembic hiện tại của DB (rỗng nếu chưa có bảng / postgres không chạy)
db_revision() {
  psql_q "SELECT string_agg(version_num, ',' ORDER BY version_num) FROM alembic_version" 2>/dev/null || true
}

# healthy | starting | running | unhealthy | restarting | exited | dead | missing ...
container_health() {
  local id
  id="$(docker compose ps -aq "$1" 2>/dev/null)"
  [[ -n "$id" ]] || { echo "missing"; return; }
  docker inspect --format \
    '{{if eq .State.Status "running"}}{{if .State.Health}}{{.State.Health.Status}}{{else}}running{{end}}{{else}}{{.State.Status}}{{end}}' \
    "$id"
}

# 0 = backend healthy; 1 = lỗi (unhealthy, crash/restart liên tục, hết giờ)
wait_backend_healthy() {
  local deadline=$((SECONDS + HEALTH_TIMEOUT_SECONDS)) status
  while :; do
    status="$(container_health backend)"
    case "$status" in
      healthy) return 0 ;;
      unhealthy|restarting|exited|dead|missing) log "backend: $status"; return 1 ;;
    esac
    (( SECONDS < deadline )) || { log "backend chưa healthy sau ${HEALTH_TIMEOUT_SECONDS}s (đang: $status)"; return 1; }
    sleep 5
  done
}

PREV_BACKEND="$(env_value BACKEND_TAG)"
PREV_FRONTEND="$(env_value FRONTEND_TAG)"
API_DOMAIN="$(env_value API_DOMAIN)"
log "Version hiện tại: backend=${PREV_BACKEND:-<trống>} frontend=${PREV_FRONTEND:-<trống>} -> mới: $VERSION"

# ---------- 1. Backup DB + ghi lại revision ----------
mkdir -p "$BACKUP_DIR"
BACKUP_FILE=""
PREV_REVISION=""
if docker compose ps --status running --services 2>/dev/null | grep -qx postgres; then
  PREV_REVISION="$(db_revision)"
  BACKUP_FILE="$BACKUP_DIR/before-${VERSION}-$(date +%Y%m%d-%H%M%S).dump"
  log "Backup DB (revision ${PREV_REVISION:-<chưa có>}) -> $BACKUP_FILE"
  docker compose exec -T postgres pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_FILE"
  [[ -s "$BACKUP_FILE" ]] || die "file backup rỗng, dừng deploy"
  # Giữ KEEP_BACKUPS bản mới nhất
  { ls -1t "$BACKUP_DIR"/*.dump 2>/dev/null || true; } | tail -n +"$((KEEP_BACKUPS + 1))" | xargs -r rm -f
else
  log "Postgres chưa chạy -> bỏ qua backup (lần deploy đầu tiên?)"
fi

# ---------- 2. Rollback khi lỗi ----------
# Khôi phục backup vào DB tạm, rồi đổi tên: DB lỗi được GIỮ LẠI (ChamCodeDB_failed_*)
# để điều tra; bảng do migration mới tạo cũng không còn sót trong DB đang dùng.
restore_db() {
  local tmp_db="${DB_NAME}_restore" failed_db
  failed_db="${DB_NAME}_failed_$(date +%Y%m%d%H%M%S)"
  log "Khôi phục DB từ $BACKUP_FILE (DB hiện tại đổi tên thành $failed_db)"
  docker compose stop backend > /dev/null 2>&1 || true
  psql_q "DROP DATABASE IF EXISTS \"$tmp_db\"" postgres \
    && psql_q "CREATE DATABASE \"$tmp_db\"" postgres \
    && docker compose exec -T postgres pg_restore -U "$DB_USER" -d "$tmp_db" --no-owner --exit-on-error < "$BACKUP_FILE" \
    && psql_q "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid()" postgres > /dev/null \
    && psql_q "ALTER DATABASE \"$DB_NAME\" RENAME TO \"$failed_db\"" postgres \
    && psql_q "ALTER DATABASE \"$tmp_db\" RENAME TO \"$DB_NAME\"" postgres
}

rollback() {
  trap - ERR
  set +e
  log "Deploy $VERSION thất bại -> quay về backend=${PREV_BACKEND:-?} frontend=${PREV_FRONTEND:-?}"
  log "--- 60 dòng log cuối của backend $VERSION ---"
  docker compose logs --tail 60 backend

  if [[ -z "$PREV_BACKEND" || -z "$PREV_FRONTEND" ]]; then
    log "Không có version trước để quay về (lần deploy đầu tiên). Cần xử lý tay."
    exit "$EXIT_ROLLBACK_FAILED"
  fi

  # Bản lỗi đã migrate DB => image cũ chạy `alembic upgrade head` sẽ crash
  # ("Can't locate revision"), nên phải đưa DB về trước khi chạy image cũ.
  local cur_rev
  cur_rev="$(db_revision)"
  if [[ -n "$PREV_REVISION" && -n "$cur_rev" && "$cur_rev" != "$PREV_REVISION" ]]; then
    log "Bản $VERSION đã migrate DB: $PREV_REVISION -> $cur_rev"
    if [[ -z "$BACKUP_FILE" ]] || ! restore_db; then
      log "KHÔNG khôi phục được DB -> không chạy image cũ (sẽ crash). Production đang ở trạng thái lỗi, cần xử lý tay."
      exit "$EXIT_ROLLBACK_FAILED"
    fi
    log "Đã khôi phục DB về revision $PREV_REVISION. Dữ liệu ghi trong lúc bản $VERSION chạy đã mất (còn trong DB *_failed_*)."
  fi

  set_tag BACKEND_TAG "$PREV_BACKEND"
  set_tag FRONTEND_TAG "$PREV_FRONTEND"
  if ! docker compose up -d --remove-orphans; then
    log "up -d với version cũ cũng lỗi, cần xử lý tay"
    exit "$EXIT_ROLLBACK_FAILED"
  fi
  if wait_backend_healthy; then
    log "ĐÃ QUAY VỀ $PREV_BACKEND, backend healthy"
    exit "$EXIT_ROLLED_BACK"
  fi
  log "Đã chạy lại $PREV_BACKEND nhưng backend KHÔNG healthy. Cần xử lý tay."
  docker compose logs --tail 60 backend
  exit "$EXIT_ROLLBACK_FAILED"
}

# ---------- 3. Đổi tag, pull, chạy ----------
set_tag BACKEND_TAG "$VERSION"
set_tag FRONTEND_TAG "$VERSION"
# Từ đây mọi lỗi ngoài dự kiến cũng phải rollback, không để server dở dang
trap rollback ERR

docker compose config --quiet || rollback

log "Pull image $VERSION"
docker compose pull backend frontend || rollback

log "docker compose up -d"
docker compose up -d --remove-orphans || rollback

# Caddy không tự đọc lại Caddyfile khi file đổi (CD tải bản mới từ repo mỗi lần deploy)
docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile > /dev/null 2>&1 \
  || log "Cảnh báo: caddy reload lỗi, Caddy vẫn chạy với cấu hình cũ"

# ---------- 4. Kiểm tra sức khoẻ ----------
log "Chờ backend healthy (tối đa ${HEALTH_TIMEOUT_SECONDS}s, gồm cả alembic upgrade head)"
wait_backend_healthy || rollback
log "Backend healthy (DB revision: $(db_revision))"

log "Kiểm tra frontend trả lời trong container"
frontend_ok=false
for _ in $(seq 1 12); do
  if docker compose exec -T frontend wget -q -O /dev/null http://127.0.0.1:3000/; then
    frontend_ok=true
    break
  fi
  sleep 5
done
$frontend_ok || rollback

if [[ -n "$API_DOMAIN" ]]; then
  log "Kiểm tra API public https://$API_DOMAIN/"
  curl -fsS --max-time 10 --retry 5 --retry-delay 3 --retry-all-errors "https://$API_DOMAIN/" > /dev/null || rollback
fi

trap - ERR
docker image prune -f > /dev/null || true
log "Trạng thái:"
docker compose ps --format 'table {{.Service}}\t{{.Image}}\t{{.Status}}'
log "DEPLOY THÀNH CÔNG: $VERSION"
