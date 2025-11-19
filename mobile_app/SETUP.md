# Hướng dẫn Setup Mobile App

## Bước 1: Cài đặt Backend API

### 1.1. Cài đặt dependencies

```bash
pip install djangorestframework django-cors-headers
```

Hoặc thêm vào `requirements.txt`:
```
djangorestframework>=3.14.0
django-cors-headers>=4.3.0
```

### 1.2. Chạy migrations cho API app

```bash
python manage.py makemigrations api
python manage.py migrate
```

### 1.3. Test API

Khởi động server:
```bash
python manage.py runserver
```

Test API endpoint:
```bash
# Xem danh sách equipment (cần đăng nhập)
curl http://localhost:8000/api/equipment/

# Đăng nhập
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

## Bước 2: Setup Android App

### 2.1. Yêu cầu

- Android Studio Hedgehog (2023.1.1) hoặc mới hơn
- JDK 17
- Android SDK 24+ (Android 7.0+)

### 2.2. Import Project

1. Mở Android Studio
2. File > Open > Chọn folder `mobile_app/android/`
3. Đợi Gradle sync hoàn tất

### 2.3. Cấu hình API Endpoint

Sửa file `app/src/main/java/com/company/equipment/utils/Config.kt`:

```kotlin
object Config {
    // Thay đổi URL này thành server của bạn
    const val API_BASE_URL = "http://192.168.1.100:8000/api/"
    const val API_TIMEOUT = 30L
}
```

**Lưu ý:** 
- Nếu chạy trên emulator: dùng `http://10.0.2.2:8000/api/` (Android emulator localhost)
- Nếu chạy trên thiết bị thật: dùng IP của máy tính (ví dụ: `http://192.168.1.100:8000/api/`)
- Đảm bảo điện thoại và máy tính cùng mạng WiFi

### 2.4. Build và Run

1. Kết nối thiết bị Android hoặc khởi động emulator
2. Click Run (Shift+F10) hoặc Build > Run
3. Chọn thiết bị và chờ app cài đặt

## Bước 3: Cấu hình CORS (nếu cần)

Nếu gặp lỗi CORS khi test từ browser, thêm vào `settings.py`:

```python
# Cho phép tất cả origins trong development (KHÔNG dùng trong production!)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
```

## Bước 4: Tạo User để test

```bash
python manage.py createsuperuser
```

Hoặc tạo user thông thường:
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
user = User.objects.create_user('testuser', 'test@example.com', 'password123')
user.save()
```

## Troubleshooting

### Lỗi: "Connection refused"

- Kiểm tra server Django đang chạy: `python manage.py runserver`
- Kiểm tra URL trong `Config.kt` đúng chưa
- Kiểm tra firewall không chặn port 8000

### Lỗi: "CORS policy"

- Đảm bảo đã cài `django-cors-headers`
- Kiểm tra `CORS_ALLOWED_ORIGINS` trong `settings.py`
- Thử thêm `CORS_ALLOW_ALL_ORIGINS = True` trong development

### Lỗi: "401 Unauthorized"

- Đảm bảo đã đăng nhập trước khi gọi API
- Kiểm tra username/password đúng chưa
- Kiểm tra session authentication hoạt động

### Android: "Network Security Config"

Nếu dùng HTTP (không phải HTTPS), cần thêm vào `AndroidManifest.xml`:

```xml
<application
    ...
    android:usesCleartextTraffic="true">
    ...
</application>
```

## API Documentation

Sau khi setup xong, truy cập:
- API Root: http://localhost:8000/api/
- Equipment List: http://localhost:8000/api/equipment/
- Tickets: http://localhost:8000/api/tickets/
- NAS Logs: http://localhost:8000/api/nas-logs/

## Next Steps

1. Tạo các màn hình Android (UI)
2. Implement API calls với Retrofit
3. Setup Room database cho offline caching
4. Implement authentication flow
5. Test trên thiết bị thật



