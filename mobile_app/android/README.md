# Android App - Hệ thống Quản lý Thiết bị IT

Ứng dụng Android được xây dựng bằng Kotlin và Material Design.

## Cấu trúc Project

```
android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/company/equipment/
│   │   │   │   ├── ui/
│   │   │   │   │   ├── equipment/      # Màn hình quản lý thiết bị
│   │   │   │   │   ├── nas/            # Màn hình quản lý NAS
│   │   │   │   │   ├── tickets/        # Màn hình tickets
│   │   │   │   │   ├── renewals/       # Màn hình gia hạn
│   │   │   │   │   └── auth/           # Màn hình đăng nhập
│   │   │   │   ├── data/
│   │   │   │   │   ├── api/            # Retrofit API clients
│   │   │   │   │   ├── database/       # Room database
│   │   │   │   │   └── repository/     # Repository pattern
│   │   │   │   ├── model/              # Data models
│   │   │   │   └── utils/              # Utilities
│   │   │   └── res/                    # Resources
│   │   └── test/                       # Unit tests
│   └── build.gradle
├── build.gradle
└── settings.gradle
```

## Cài đặt

1. Mở Android Studio
2. File > Open > Chọn folder `mobile_app/android/`
3. Sync Gradle
4. Cấu hình API endpoint trong `Config.kt`
5. Build và Run

## Cấu hình

### API Endpoint

Sửa file `app/src/main/java/com/company/equipment/utils/Config.kt`:

```kotlin
object Config {
    const val API_BASE_URL = "http://your-server.com/api/"
    const val API_TIMEOUT = 30L // seconds
}
```

### Dependencies

- Retrofit 2.9.0 - HTTP client
- Room 2.5.0 - Local database
- Coroutines - Async operations
- Material Design Components
- Navigation Component
- ViewBinding

## Tính năng

### 1. Authentication
- Đăng nhập/Đăng xuất
- Lưu session
- Auto refresh token

### 2. Equipment Management
- Danh sách thiết bị
- Tìm kiếm và lọc
- Chi tiết thiết bị
- Thêm/Sửa/Xóa thiết bị
- Xem lịch sử thiết bị
- Upload DxDiag.txt

### 3. NAS Management
- Danh sách NAS
- Xem logs
- Dashboard statistics

### 4. Tickets
- Danh sách tickets
- Tạo ticket mới
- Cập nhật trạng thái
- Chi tiết ticket

### 5. Renewals
- Danh sách gia hạn
- Thêm gia hạn mới
- Cảnh báo sắp hết hạn

## Build

```bash
# Debug build
./gradlew assembleDebug

# Release build
./gradlew assembleRelease
```

## Notes

- Minimum SDK: 24 (Android 7.0)
- Target SDK: 34 (Android 14)
- Kotlin version: 1.9.0+



