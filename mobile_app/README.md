# Mobile App - Hệ thống Quản lý Thiết bị IT

Thư mục này chứa ứng dụng Android cho hệ thống quản lý thiết bị IT.

## Cấu trúc

```
mobile_app/
├── android/              # Android project (Kotlin/Java)
│   ├── app/
│   ├── build.gradle
│   └── settings.gradle
├── api/                 # Django REST API backend
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── permissions.py
└── README.md
```

## Tính năng Mobile App

### 1. Quản lý Thiết bị (Equipment)
- ✅ Xem danh sách thiết bị
- ✅ Tìm kiếm và lọc thiết bị
- ✅ Xem chi tiết thiết bị
- ✅ Thêm/sửa/xóa thiết bị
- ✅ Xem lịch sử thiết bị
- ✅ Upload DxDiag.txt (từ Android)

### 2. Quản lý NAS
- ✅ Xem danh sách NAS
- ✅ Xem logs NAS
- ✅ Dashboard logs
- ✅ Quản lý file trên NAS

### 3. Ticket Hỗ trợ
- ✅ Xem danh sách tickets
- ✅ Tạo ticket mới
- ✅ Cập nhật trạng thái ticket
- ✅ Xem chi tiết ticket

### 4. Gia hạn Dịch vụ (Renewals)
- ✅ Xem danh sách gia hạn
- ✅ Thêm gia hạn mới
- ✅ Cảnh báo sắp hết hạn

## Cài đặt

### Backend API

1. Cài đặt Django REST Framework:
```bash
pip install djangorestframework
pip install django-cors-headers
```

2. Thêm vào `INSTALLED_APPS` trong `settings.py`:
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'corsheaders',
    'api',  # API app
]
```

3. Thêm CORS middleware:
```python
MIDDLEWARE = [
    ...
    'corsheaders.middleware.CorsMiddleware',
    ...
]
```

4. Cấu hình CORS:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True
```

### Android App

1. Mở Android Studio
2. Import project từ `mobile_app/android/`
3. Sync Gradle
4. Cấu hình API endpoint trong `Config.kt`
5. Build và chạy

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Đăng nhập
- `POST /api/auth/logout/` - Đăng xuất
- `GET /api/auth/user/` - Thông tin user hiện tại

### Equipment
- `GET /api/equipment/` - Danh sách thiết bị
- `GET /api/equipment/{id}/` - Chi tiết thiết bị
- `POST /api/equipment/` - Tạo thiết bị mới
- `PUT /api/equipment/{id}/` - Cập nhật thiết bị
- `DELETE /api/equipment/{id}/` - Xóa thiết bị
- `GET /api/equipment/{id}/history/` - Lịch sử thiết bị

### NAS
- `GET /api/nas/` - Danh sách NAS
- `GET /api/nas/{id}/logs/` - Logs của NAS
- `GET /api/nas/{id}/dashboard/` - Dashboard NAS

### Tickets
- `GET /api/tickets/` - Danh sách tickets
- `POST /api/tickets/` - Tạo ticket mới
- `GET /api/tickets/{id}/` - Chi tiết ticket
- `PUT /api/tickets/{id}/` - Cập nhật ticket

### Renewals
- `GET /api/renewals/` - Danh sách gia hạn
- `POST /api/renewals/` - Tạo gia hạn mới

## Công nghệ sử dụng

### Backend
- Django REST Framework
- Django CORS Headers
- JWT Authentication (tùy chọn)

### Android
- Kotlin
- Retrofit (HTTP client)
- Room Database (local caching)
- Material Design Components
- Coroutines (async operations)

## Development

### Chạy API server
```bash
python manage.py runserver
```

### Test API
```bash
# Xem danh sách equipment
curl http://localhost:8000/api/equipment/

# Đăng nhập
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

## Notes

- API sử dụng token authentication hoặc session authentication
- Android app cache dữ liệu local để offline access
- Sync dữ liệu khi có kết nối internet



