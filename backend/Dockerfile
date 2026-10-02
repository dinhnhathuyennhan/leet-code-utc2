FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Cài dependency trước để tận dụng layer cache khi chỉ sửa code
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Không chạy app bằng root
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Render truyền cổng qua biến PORT (mặc định 10000); chạy local thì dùng 8000
EXPOSE 8000

# Chạy migration rồi mới khởi động server.
# --proxy-headers: Render đứng sau reverse proxy, cần đọc X-Forwarded-* để biết scheme/IP thật.
# Số worker lấy từ biến WEB_CONCURRENCY (uvicorn tự đọc), mặc định 1.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
