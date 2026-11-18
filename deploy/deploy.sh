#!/usr/bin/env bash
# Deploy một version lên EC2 chamcode-app.
#
#   bash /opt/chamcode/deploy.sh <version>        ví dụ: bash deploy.sh 1.0.0
#
# Pipeline CD (.github/workflows/cd.yaml) gọi script này qua AWS SSM; chạy tay
# trên server cũng được (user ubuntu). Các bước:
#   1. kiểm tra version + .env, khoá để không có 2 lần deploy chạy song song
#   2. backup Postgres trước khi đổi gì (giữ KEEP_BACKUPS bản mới nhất)
#   3. ghi BACKEND_TAG/FRONTEND_TAG mới vào .env, pull image, up -d
#   4. chờ backend healthy + frontend trả lời + API public qua HTTPS
#   5. lỗi ở bước 3–4 => tự quay về tag cũ (KHÔNG tự restore DB, xem log)
#
# Script không in nội dung .env (repo public => log của GitHub Actions public).

set -Eeuo pipefail

VERSION="${1:-}"
APP_DIR="${APP_DIR:-/opt/chamcode}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
KEEP_BACKUPS="${KEEP_BACKUPS:-10}"
HEALTH_TIMEOUT_SECONDS="${HEALTH_TIMEOUT_SECONDS:-240}"

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

PREV_BACKEND="$(env_value BACKEND_TAG)"
PREV_FRONTEND="$(env_value FRONTEND_TAG)"
API_DOMAIN="$(env_value API_DOMAIN)"
log "Version hiện tại: backend=${PREV_BACKEND:-<trống>} frontend=${PREV_FRONTEND:-<trống>} -> mới: $VERSION"

# ---------- 1. Backup DB ----------
mkdir -p "$BACKUP_DIR"
BACKUP_FILE=""
if docker compose ps --status running --services 2>/dev/null | grep -qx postgres; then
  BACKUP_FILE="$BACKUP_DIR/before-${VERSION}-$(date +%Y%m%d-%H%M%S).dump"
  log "Backup DB -> $BACKUP_FILE"
  docker compose exec -T postgres pg_dump -U chamcode -Fc ChamCodeDB > "$BACKUP_FILE"
  [[ -s "$BACKUP_FILE" ]] || die "file backup rỗng, dừng deploy"
  # Giữ KEEP_BACKUPS bản mới nhất
  { ls -1t "$BACKUP_DIR"/*.dump 2>/dev/null || true; } | tail -n +"$((KEEP_BACKUPS + 1))" | xargs -r rm -f
else
  log "Postgres chưa chạy -> bỏ qua backup (lần deploy đầu tiên?)"
fi

# ---------- 2. Rollback khi lỗi ----------
rollback() {
  log "Deploy $VERSION thất bại -> quay về backend=$PREV_BACKEND frontend=$PREV_FRONTEND"
  if [[ -n "$PREV_BACKEND" && -n "$PREV_FRONTEND" ]]; then
    set_tag BACKEND_TAG "$PREV_BACKEND"
    set_tag FRONTEND_TAG "$PREV_FRONTEND"
    docker compose up -d --remove-orphans || log "up -d với tag cũ cũng lỗi, cần xử lý tay"
  fi
  log "--- 60 dòng log cuối của backend ---"
  docker compose logs --tail 60 backend || true
  if [[ -n "$BACKUP_FILE" ]]; then
    log "Nếu version lỗi đã chạy migration làm hỏng schema, restore bằng tay:"
    log "  docker compose stop backend && docker compose exec -T postgres pg_restore -U chamcode -d ChamCodeDB --clean --if-exists --no-owner < $BACKUP_FILE && docker compose start backend"
  fi
  exit 1
}

# ---------- 3. Đổi tag, pull, chạy ----------
set_tag BACKEND_TAG "$VERSION"
set_tag FRONTEND_TAG "$VERSION"
docker compose config --quiet || rollback

log "Pull image $VERSION"
docker compose pull backend frontend || rollback

log "docker compose up -d"
docker compose up -d --remove-orphans || rollback

# Caddy không tự đọc lại Caddyfile khi file đổi (CD tải bản mới từ repo mỗi lần deploy)
docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile > /dev/null 2>&1 \
  || log "Cảnh báo: caddy reload lỗi, Caddy vẫn chạy với cấu hình cũ"

# ---------- 4. Kiểm tra sức khoẻ ----------
container_health() {
  local id
  id="$(docker compose ps -q "$1")"
  [[ -n "$id" ]] || { echo "missing"; return; }
  docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$id"
}

log "Chờ backend healthy (tối đa ${HEALTH_TIMEOUT_SECONDS}s, gồm cả alembic upgrade head)"
deadline=$((SECONDS + HEALTH_TIMEOUT_SECONDS))
until [[ "$(container_health backend)" == "healthy" ]]; do
  status="$(container_health backend)"
  [[ "$status" == "unhealthy" || "$status" == "exited" || "$status" == "missing" ]] && rollback
  (( SECONDS < deadline )) || rollback
  sleep 5
done
log "Backend healthy"

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

docker image prune -f > /dev/null || true
log "Trạng thái:"
docker compose ps --format 'table {{.Service}}\t{{.Image}}\t{{.Status}}'
log "DEPLOY THÀNH CÔNG: $VERSION"
