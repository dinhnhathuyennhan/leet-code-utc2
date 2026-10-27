#!/bin/sh
set -eu

# Cổng proxy HTTP outbound của Tailscale. Service AI review đọc TS_PROXY_URL;
# entrypoint tự export sau khi Tailscale lên, để không phải khai lại biến trên
# Render (quên khai là mọi request AI đi thẳng, không qua tailnet, và fail hết).
TS_PROXY_PORT="${TS_PROXY_PORT:-1055}"

if [ -n "${TS_AUTHKEY:-}" ]; then
    echo "Starting Tailscale..."

    mkdir -p /tmp/tailscale

    tailscaled \
        --tun=userspace-networking \
        --state=/tmp/tailscale/tailscaled.state \
        --socket=/tmp/tailscale/tailscaled.sock \
        --outbound-http-proxy-listen=127.0.0.1:"$TS_PROXY_PORT" \
        &
    tailscaled_pid=$!

    echo "Waiting for Tailscale daemon..."

    i=0
    until [ -S /tmp/tailscale/tailscaled.sock ]; do
        # tailscaled chết ngay (sai flag, thiếu quyền) thì báo luôn,
        # không chờ hết 30 giây rồi mới bảo "socket not available".
        if ! kill -0 "$tailscaled_pid" 2>/dev/null; then
            echo "ERROR: tailscaled đã thoát sớm"
            exit 1
        fi

        i=$((i + 1))

        if [ "$i" -ge 30 ]; then
            echo "ERROR: Tailscale socket not available"
            exit 1
        fi

        sleep 1
    done

    echo "Authenticating Tailscale..."

    # State nằm trong /tmp nên mỗi lần container khởi động là một node mới trong
    # tailnet; dùng auth key ephemeral để node cũ tự biến mất, nếu không hostname
    # sẽ bị đổi thành render-fastapi-1, -2... sau mỗi lần deploy.
    tailscale \
        --socket=/tmp/tailscale/tailscaled.sock \
        up \
        --auth-key="$TS_AUTHKEY" \
        --hostname=render-fastapi

    echo "Tailscale connected."

    export TS_PROXY_URL="${TS_PROXY_URL:-http://127.0.0.1:$TS_PROXY_PORT}"
fi

echo "Running database migrations..."

gosu appuser alembic upgrade head

if [ "$#" -gt 0 ]; then
    exec gosu appuser "$@"
fi

echo "Starting FastAPI..."

exec gosu appuser uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --proxy-headers \
    --forwarded-allow-ips="*"
