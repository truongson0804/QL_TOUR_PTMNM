FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GDAL_CONFIG=/usr/bin/gdal-config

RUN apt-get update && apt-get install -y \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 1. KHAI BÁO PORT ĐỂ RENDER QUÉT (Mặc định Render khuyên dùng 10000)
EXPOSE 10000

# 2. SỬ DỤNG LỆNH CHẠY ĐỘNG THEO BIẾN $PORT CỦA RENDER
# Sử dụng 'sh -c' để Docker có thể hiểu và truyền được biến môi trường $PORT vào lệnh chạy Django
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py makemigrations && python manage.py migrate && python create_admin.py && python manage.py runserver 0.0.0.0:${PORT:-10000}"]