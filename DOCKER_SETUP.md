# 🐳 Hướng Dẫn Cài Đặt & Chạy Dự Án Bằng Docker

Hướng dẫn chi tiết để cài đặt và chạy dự án QL TOUR bằng Docker & Docker Compose.

## 📋 Yêu Cầu Hệ Thống

- **Docker**: Phiên bản 20.10.x trở lên
- **Docker Compose**: Phiên bản 2.0 trở lên
- **Git**: Để clone repository
- **RAM**: Tối thiểu 2GB
- **Disk Space**: Tối thiểu 2GB cho images và containers

### Kiểm Tra Cài Đặt

```bash
docker --version
docker compose version
git --version
```

## 🚀 Bước 1: Clone Repository

```bash
# Clone dự án
git clone https://github.com/truongson0804/QL_TOUR_PTMNM.git

# Di chuyển vào thư mục dự án
cd QL_TOUR_PTMNM
```

## 🔧 Bước 2: Cấu Hình Environment

Tạo file `.env` trong thư mục gốc dự án:

```bash
# Tạo file .env
cp .env.example .env  # Nếu có file mẫu
# Hoặc tạo thủ công
nano .env
```

Thêm các biến môi trường sau vào `.env`:

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=qltour_db
DB_USER=qltour_user
DB_PASSWORD=secure-password-change-this
DB_HOST=db
DB_PORT=5432

# Django User (superuser)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin-password-change-this
```

### 📌 Lưu Ý Bảo Mật

- **NEVER** commit file `.env` lên Git
- Thay đổi `SECRET_KEY` thành một giá trị ngẫu nhiên
- Sử dụng mật khẩu mạnh cho `DB_PASSWORD`
- Trong production, sử dụng `.env` từ hệ thống hoặc container secrets

## 🐳 Bước 3: Khởi Động Docker Compose

### Lần Đầu Tiên (Build Images)

```bash
# Build images và khởi động containers
docker compose up -d --build

# Hoặc không build lại nếu images đã có
docker compose up -d
```

### Kiểm Tra Status

```bash
# Xem trạng thái các services
docker compose ps

# Xem logs từ web service
docker compose logs -f web

# Xem logs từ database
docker compose logs -f db
```

## 🔄 Bước 4: Chạy Migrations & Setup

```bash
# Chạy database migrations
docker compose exec web python manage.py migrate

# Tạo thư mục static files
docker compose exec web python manage.py collectstatic --noinput

# Tạo superuser (admin) - Lựa chọn 1
# Cách 1: Interactive (nhập từng bước)
docker compose exec web python manage.py createsuperuser

# Cách 2: Non-interactive (từ biến môi trường .env)
docker compose exec web python manage.py createsuperuser --noinput \
  --username=$DJANGO_SUPERUSER_USERNAME \
  --email=$DJANGO_SUPERUSER_EMAIL
```

## ✅ Bước 5: Truy Cập Ứng Dụng

Mở trình duyệt và truy cập:

| Trang        | URL                                  | Ghi Chú                 |
| ------------ | ------------------------------------ | ----------------------- |
| Trang Chủ    | `http://localhost:8000`              | Trang chủ chính         |
| Admin Django | `http://localhost:8000/admin`        | Quản lý Django          |
| Admin Panel  | `http://localhost:8000/admin-panel/` | Dashboard quản lý       |
| Database     | `localhost:5432`                     | PostgreSQL (nếu expose) |

### Đăng Nhập Admin

- **Username**: `admin` (hoặc tên bạn cấu hình)
- **Password**: `admin-password-change-this` (hoặc mật khẩu bạn cấu hình)

## 🛑 Bước 6: Dừng & Xóa Containers

```bash
# Dừng tất cả containers (giữ data)
docker compose down

# Dừng và xóa tất cả (xóa volumes & data)
docker compose down -v

# Chỉ dừng services
docker compose stop

# Khởi động lại
docker compose start
```

## 📊 Các Lệnh Docker Compose Hữu Ích

```bash
# Xem logs thời gian thực từ web service
docker compose logs -f web

# Xem logs từ database
docker compose logs -f db

# Truy cập shell Django
docker compose exec web python manage.py shell

# Truy cập terminal trong web container
docker compose exec web /bin/bash

# Chạy manage.py commands
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Dump/Restore database
# Backup database
docker compose exec db pg_dump -U qltour_user qltour_db > backup.sql

# Restore database
cat backup.sql | docker compose exec -T db psql -U qltour_user qltour_db
```

## 🔧 Quản Lý Dữ Liệu

### Truy Cập Database PostgreSQL

```bash
# Kết nối tới database bằng psql
docker compose exec db psql -U qltour_user -d qltour_db

# Hoặc sử dụng pgAdmin (nếu có trong docker-compose)
# Truy cập http://localhost:5050
```

### Load Sample Data

```bash
# Nếu có fixture files
docker compose exec web python manage.py loaddata fixtures/sample_data.json

# Hoặc tạo dữ liệu mẫu qua shell
docker compose exec web python manage.py shell
```

## 🚨 Troubleshooting

### ❌ Lỗi: "Port 8000 already in use"

```bash
# Tìm process sử dụng port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Dừng process hoặc thay đổi port trong docker-compose.yml
```

### ❌ Lỗi: "Cannot connect to database"

```bash
# Kiểm tra logs database
docker compose logs db

# Kiểm tra services đang chạy
docker compose ps

# Restart database service
docker compose restart db
```

### ❌ Lỗi: "Static files not loading"

```bash
# Collect static files lại
docker compose exec web python manage.py collectstatic --noinput

# Kiểm tra thư mục staticfiles
docker compose exec web ls -la /app/staticfiles/
```

### ❌ Lỗi: "Module not found / Import Error"

```bash
# Cài đặt dependencies lại
docker compose exec web pip install -r requirements.txt

# Hoặc rebuild image
docker compose up -d --build
```

### ❌ Lỗi: "Permission denied"

```bash
# Kiểm tra quyền thư mục
ls -la

# Fix quyền (nếu cần)
chmod -R 755 ./
```

## 🔐 Environment Variables Toàn Diện

```env
# ===== DJANGO SETTINGS =====
DEBUG=False                                    # Disable debug mode in production
SECRET_KEY=your-very-long-random-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,example.com
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# ===== DATABASE =====
DB_ENGINE=django.db.backends.postgresql
DB_NAME=qltour_db
DB_USER=qltour_user
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# ===== DJANGO SUPERUSER =====
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password

# ===== EMAIL (Optional) =====
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# ===== STATIC & MEDIA =====
STATIC_URL=/static/
MEDIA_URL=/media/
```

## 📈 Performance Tips

### Để Tối Ưu Hóa

1. **Increase Docker Resources**: Cấp phát nhiều CPU/RAM hơn cho Docker
2. **Database Indexing**: Tạo indexes trên các cột thường xuyên query
3. **Caching**: Cân nhắc sử dụng Redis cache layer
4. **Reverse Proxy**: Sử dụng Nginx để serve static files
5. **Load Testing**: Kiểm tra hiệu suất với tools như Apache Bench

## 🔄 Production Deployment

Để deploy lên production:

```bash
# 1. Cấu hình .env với các giá trị production
DEBUG=False
SECRET_KEY=<production-secret-key>
ALLOWED_HOSTS=yourdomain.com

# 2. Update docker-compose.yml cho production
# - Expose ports thích hợp
# - Setup volume persistence cho database
# - Configure logging

# 3. Khởi động
docker compose -f docker-compose.yml up -d

# 4. Setup SSL/HTTPS (nếu cần)
# - Sử dụng Nginx reverse proxy
# - Cấu hình Let's Encrypt certificates
```

## 📞 Cần Hỗ Trợ?

1. Kiểm tra logs: `docker compose logs -f`
2. Xem file cấu hình: `docker-compose.yml`, `Dockerfile`, `.env`
3. Kiểm tra requirements.txt: Đảm bảo tất cả dependencies được install
4. Tạo issue trên GitHub nếu gặp vấn đề

---

**Cập nhật lần cuối**: May 18, 2026  
**Version**: 1.0
