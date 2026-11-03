#!/bin/bash
#
# security-regression.sh
#
# Bước 10: Biến lỗ hổng thành test tự động (Security Regression)
#
# Mục tiêu: mỗi lỗ hổng đã phát hiện phải có test tự động để không "tái phát lặng lẽ".
# Test này nhắm vào SQLi tại endpoint đăng nhập của OWASP Juice Shop.
#
#   BASE_URL   : mặc định http://localhost:3000 (override bằng env var)
#   CURL       : override curl nếu cần
#
# Chạy:  chmod +x security-regression.sh && ./security-regression.sh
#        (hoặc: bash security-regression.sh)

set -u

BASE="${BASE_URL:-http://localhost:3000}"
CURL="${CURL:-curl}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=0

# printf de hien thi dung escape sequence (echo trong sh khong interpret \033)
say()  { printf "%b\n" "$1"; }
title() { printf "${BOLD}${CYAN}%s${NC}\n" "$1"; }
line()  { printf "${CYAN}%s${NC}\n" "$1"; }
ok()    { printf "${GREEN}%s${NC}\n" "$1"; }
warn()  { printf "${YELLOW}%s${NC}\n" "$1"; }
err()   { printf "${RED}%s${NC}\n" "$1"; }

# ---------------------------------------------------------------------------
# login_status <email> [password]
# Gui POST /rest/user/login va tra ve HTTP status code (chi so).
# ---------------------------------------------------------------------------
login_status() {
    local email="$1"
    local password="${2:-anything123}"
    local payload
    payload=$(printf '{"email":"%s","password":"%s"}' "$email" "$password")
    "$CURL" -s -o /dev/null -w '%{http_code}' \
        -X POST "$BASE/rest/user/login" \
        -H 'Content-Type: application/json' \
        --data "$payload"
}

# ---------------------------------------------------------------------------
# check <mo ta> <ky vong> <thuc te>
# ---------------------------------------------------------------------------
check() {
    local desc="$1" expected="$2" actual="$3"
    TOTAL=$((TOTAL + 1))
    if [ "$actual" = "$expected" ]; then
        printf "  ${GREEN}[PASS]${NC} %-44s HTTP %s\n" "$desc" "$actual"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        printf "  ${RED}[FAIL]${NC} %-44s HTTP %s (ky vong %s)\n" "$desc" "$actual" "$expected"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

printf "${BOLD}${CYAN}"
printf "==============================================================\n"
printf "  SECURITY REGRESSION TEST - OWASP Juice Shop\n"
printf "  Target: %s/rest/user/login\n" "$BASE"
printf "==============================================================\n"
printf "${NC}\n"
echo

# --- Kiem tra server con song khong -----------------------------------------
warn "[*] Kiem tra target co hoat dong khong..."
health=$(login_status "healthcheck@invalid.local")
if [ "$health" = "000" ] || [ -z "$health" ]; then
    err "[X] Khong ket noi duoc $BASE - hay khoi dong Juice Shop truoc"
    say "    docker run -p 3000:3000 bkimminich/juice-shop"
    exit 2
fi
ok "[OK] Target phan hoi (HTTP $health)"
echo

# --- Cac test case ----------------------------------------------------------
title "Test case 1: sai mat khau phai tra 401"
check "sai mat khau (admin@juice-sh.op) -> 401"  401 "$(login_status 'admin@juice-sh.op')"
check "email khong ton tai -> 401"                401 "$(login_status 'khong.ton.tai@utc2.edu.vn')"
check "email rong -> 401"                         401 "$(login_status '')"
echo

title "Test case 2: SQL injection phai bi chan (401)"
check "' OR 1=1-- -> 401"           401 "$(login_status "' OR 1=1--")"
check "' OR '1'='1 -> 401"          401 "$(login_status "' OR '1'='1")"
check "admin@juice-sh.op'-- -> 401" 401 "$(login_status "admin@juice-sh.op'--")"
check "' UNION SELECT NULL-- -> 401" 401 "$(login_status "' UNION SELECT NULL--")"
check "1' OR 1=1# -> 401"           401 "$(login_status "1' OR 1=1#")"
echo

title "Test case 3: payload SQLi o truong password"
check "email hop le + password SQLi -> 401" 401 "$(login_status 'admin@juice-sh.op' "' OR 1=1--")"
echo

# --- Tong ket ---------------------------------------------------------------
printf "${BOLD}${CYAN}"
printf "==============================================================\n"
printf "${NC}"
if [ "$FAIL_COUNT" -eq 0 ]; then
    printf "${BOLD}${GREEN}  KET QUA: %d/%d PASS - KHONG co hoi quy loi ho${NC}\n" "$PASS_COUNT" "$TOTAL"
else
    printf "${BOLD}${RED}  KET QUA: %d/%d PASS - %d FAIL${NC}\n" "$PASS_COUNT" "$TOTAL" "$FAIL_COUNT"
    echo
    warn "[!] Cac test FAIL chung to la DAU HIEU LO HONG TON TAI"
    say "    (neu Juice Shop da duoc va bang truy van tham so hoa, chung ta se thay 401)"
    say "    Day chinh la muc dich cua test regression: 'do' chung minh loi ho con ton tai."
fi
printf "${BOLD}${CYAN}"
printf "==============================================================\n"
printf "${NC}"

[ "$FAIL_COUNT" -eq 0 ] && exit 0 || exit 1
