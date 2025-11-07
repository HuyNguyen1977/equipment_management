venv\# Hướng dẫn khởi chạy nhanh

## Bước 1: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## Bước 2: Chạy migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Bước 3: Tạo superuser (tùy chọn)

```bash
python manage.py createsuperuser
```

## Bước 4: Tạo 3 công ty mặc định

```bash
python manage.py create_companies
```

Hoặc vào Django admin và tạo thủ công:
- Saigonbooks (SGB)
- Zenbooks (ZNB)
- Pegaholdings (PEG)

## Bước 5: Chạy server

```bash
python manage.py runserver
```

## Bước 6: Truy cập

- Trang chủ: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Sử dụng

### Thêm thiết bị từ DxDiag.txt

1. Vào "Thêm thiết bị"
2. Chọn công ty và loại thiết bị (Laptop hoặc Desktop)
3. Upload file DxDiag.txt
4. Hệ thống sẽ tự động điền thông tin
5. Điền thêm thông tin cần thiết và lưu

### Thêm thiết bị khác (Router, Switch, ...)

1. Vào "Thêm thiết bị"
2. Chọn công ty và loại thiết bị
3. Nhập tay các thông tin
4. Lưu

### Xem lịch sử thiết bị

1. Vào trang chi tiết thiết bị
2. Click "Xem lịch sử"
3. Xem bảng lịch sử với các cột: STT, Ngày, Nội dung chi tiết, Ký tên

