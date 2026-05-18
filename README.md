# QL TOUR - Hệ Thống Quản Lý và Đặt Tour Du Lịch

Ứng dụng web quản lý tour du lịch toàn diện với tính năng đặt tour, thanh toán, quản lý lịch trình và hệ thống admin mạnh mẽ.

## ✨ Tính Năng Chính

- **Khám phá Tours**: Duyệt danh sách tour du lịch với thông tin chi tiết, hình ảnh và lịch trình
- **Đặt Tour**: Đặt chỗ tour với các tùy chọn thanh toán linh hoạt (tiền mặt, chuyển khoản, thẻ tín dụng)
- **Quản lý Hồ Sơ**: Người dùng có thể quản lý thông tin cá nhân, xem lịch sử đặt tour
- **Admin Dashboard**: Bảng điều khiển toàn diện cho quản lý tours, đơn đặt, người dùng và doanh thu
- **Hệ Thống Danh Mục**: Phân loại tour theo lục địa, quốc gia, loại hình
- **Lịch Trình Tour**: Quản lý ngày khởi hành, ngày kết thúc, số ghế còn trống
- **Hệ Thống Thanh Toán**: Tích hợp QR code thanh toán ngân hàng
- **Quản Lý Ảnh**: Tải lên và hiển thị hình ảnh tour với gallery modal

## 🛠️ Công Nghệ Sử Dụng

- **Backend**: Django 4.x
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose
- **Template Engine**: Django Templates
- **Form Validation**: Django Forms
- **Media Storage**: File-based (local storage)

## 📁 Cấu Trúc Dự Án

```
QL_TOUR_PTMNM/
├── apps/
│   ├── admin_panel/          # Trang quản lý admin
│   ├── bookings/             # Quản lý đặt chỗ
│   ├── home/                 # Trang chủ
│   ├── payments/             # Thanh toán
│   ├── tours/                # Thông tin tour
│   └── users/                # Quản lý người dùng
├── QL_tour/                  # Cấu hình chính Django
├── templates/                # Template chung
├── static/                   # CSS, JS, hình ảnh tĩnh
├── media/                    # Hình ảnh upload từ người dùng
├── docker-compose.yml        # Cấu hình Docker Compose
├── Dockerfile                # Dockerfile
├── requirements.txt          # Python dependencies
└── manage.py                 # Django management

```

## 🚀 Bắt Đầu Nhanh với Docker

### Yêu Cầu

- Docker & Docker Compose
- Git (để clone repository)

### Hướng Dẫn Cài Đặt

Xem file **DOCKER_SETUP.md** để hướng dẫn chi tiết.

### Lệnh Nhanh

```bash
# Clone repository
git clone https://github.com/truongson0804/QL_TOUR_PTMNM.git
cd QL_TOUR_PTMNM

# Khởi động với Docker Compose
docker compose up -d

# Chạy migrations
docker compose exec web python manage.py migrate

# Tạo superuser
docker compose exec web python manage.py createsuperuser

# Truy cập ứng dụng
# Trang chủ: http://localhost:8000
# Admin: http://localhost:8000/admin
```

## 📋 Các Đường Dẫn Chính

| Trang            | URL                       |
| ---------------- | ------------------------- |
| Trang Chủ        | `/`                       |
| Danh Sách Tour   | `/tours/`                 |
| Chi Tiết Tour    | `/tours/<id>/`            |
| Đặt Tour         | `/booking/<schedule_id>/` |
| Hồ Sơ Người Dùng | `/user/profile/`          |
| Admin Panel      | `/admin/`                 |
| Quản Lý Admin    | `/admin-panel/`           |

## 👥 Quản Lý User

### Loại Tài Khoản

- **Người Dùng Thường**: Có thể duyệt tour và đặt chỗ
- **Admin**: Quản lý tours, đơn đặt, người dùng
- **Staff**: Hỗ trợ quản lý (tuỳ chọn)

### Tạo Tài Khoản Admin

```bash
docker compose exec web python manage.py createsuperuser
```

## 🔐 Bảo Mật

- Sử dụng Django CSRF Protection
- Password hashing với Django
- ALLOWED_HOSTS được cấu hình trong settings.py
- SECRET_KEY được bảo mật (sử dụng environment variables)

## 📝 Cơ Sở Dữ Liệu

### Các Model Chính

- **Tour**: Thông tin cơ bản tour
- **TourSchedule**: Lịch trình khởi hành
- **Booking**: Đơn đặt tour
- **User**: Tài khoản người dùng
- **Category**: Danh mục tour
- **Country/Continent**: Địa lý

## 📞 Support & Liên Hệ

Nếu gặp vấn đề, vui lòng:

1. Kiểm tra file **DOCKER_SETUP.md** cho troubleshooting
2. Xem logs Docker: `docker compose logs -f web`
3. Liên hệ qua GitHub Issues

## 📄 License

Dự án này không có license cụ thể. Sử dụng theo ý muốn cho mục đích cá nhân hoặc thương mại.

---

**Phiên Bản**: 1.0.0  
**Ngày Cập Nhật**: May 18, 2026
