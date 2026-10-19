#!/bin/sh
set -eu

if [ -n "${TS_AUTHKEY:-}" ]; then
    echo "Starting Tailscale..."

    mkdir -p /tmp/tailscale

    tailscaled \
        --tun=userspace-networking \
        --state=/tmp/tailscale/tailscaled.state \
        --socket=/tmp/tailscale/tailscaled.sock \
        --outbound-http-proxy-listen=127.0.0.1:1055 \
        &

    echo "Waiting for Tailscale daemon..."

    i=0
    until [ -S /tmp/tailscale/tailscaled.sock ]; do
        i=$((i + 1))

        if [ "$i" -ge 30 ]; then
            echo "ERROR: Tailscale socket not available"
            exit 1
        fi

        sleep 1
    done

    echo "Authenticating Tailscale..."

    tailscale \
        --socket=/tmp/tailscale/tailscaled.sock \
        up \
        --auth-key="$TS_AUTHKEY" \
        --hostname=render-fastapi

    echo "Tailscale connected."
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
