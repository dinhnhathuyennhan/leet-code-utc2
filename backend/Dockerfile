FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Công cụ cài Tailscale và chạy FastAPI bằng appuser
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl ca-certificates gosu && \
    curl -fsSL https://tailscale.com/install.sh -o /tmp/install-tailscale.sh && \
    sh /tmp/install-tailscale.sh && \
    rm /tmp/install-tailscale.sh && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
