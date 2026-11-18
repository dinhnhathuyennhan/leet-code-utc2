#!/usr/bin/env bash
# Cửa vào DUY NHẤT của key deploy mà GitHub Actions dùng để SSH vào EC2 chamcode-app.
#
# Cài một lần trên server (xem docs/deploy-ec2-cd.md mục 9.2):
#   /opt/chamcode/ssh-deploy.sh  (chủ sở hữu ubuntu, chmod 755)
#   ~ubuntu/.ssh/authorized_keys thêm 1 dòng:
#     restrict,command="/opt/chamcode/ssh-deploy.sh" ssh-ed25519 AAAA... github-cd
#
# Nhờ `command=`, dù client gửi lệnh gì thì sshd cũng chỉ chạy script này, lệnh gốc
# nằm trong SSH_ORIGINAL_COMMAND. Script chỉ chấp nhận đúng dạng:
#   deploy <version> <commit-sha-40-ký-tự>
# => lộ private key thì kẻ xấu cũng chỉ deploy được một commit của repo, không có shell.
#
# CD KHÔNG tự cập nhật file này (nó là chốt chặn). Sửa thì copy tay lên server.

set -Eeuo pipefail

REPO="dinhnhathuyennhan/leet-code-utc2"
APP_DIR="/opt/chamcode"
FILES=(docker-compose.prod.yml Caddyfile deploy.sh .env.prod.example)

deny() { echo "ssh-deploy: $*" >&2; exit 2; }

read -r action version sha extra <<< "${SSH_ORIGINAL_COMMAND:-}"

[[ "$action" == "deploy" && -z "$extra" ]] \
  || deny "chỉ cho phép lệnh: deploy <version> <commit-sha>"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]] \
  || deny "version không hợp lệ: '$version'"
[[ "$sha" =~ ^[0-9a-f]{40}$ ]] \
  || deny "commit sha không hợp lệ: '$sha'"

# Tải file deploy của ĐÚNG commit đang release -> cấu hình server luôn khớp git
tmp="$(mktemp -d)"
base="https://raw.githubusercontent.com/$REPO/$sha/deploy"
for f in "${FILES[@]}"; do
  curl -fsSL --retry 3 "$base/$f" -o "$tmp/$f" || { rm -rf "$tmp"; deny "không tải được $f của commit $sha"; }
done

cd "$APP_DIR"
# `cat >` thay vì mv: giữ inode, vì Caddyfile được bind mount vào container caddy
for f in "${FILES[@]}"; do
  cat "$tmp/$f" > "$f"
done
rm -rf "$tmp"
chmod 755 deploy.sh

echo "ssh-deploy: commit $sha -> version $version"
exec bash "$APP_DIR/deploy.sh" "$version"
