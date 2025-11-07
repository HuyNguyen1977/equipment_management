# Hệ thống Quản lý Thiết bị Công nghệ Thông tin

Hệ thống quản lý thiết bị IT cho 3 công ty: Saigonbooks, Zenbooks và Pegaholdings.

## Tính năng

- ✅ Quản lý thiết bị IT (Laptop, Desktop, Router, Switch, Máy in, Máy quét, ...)
- ✅ Tự động import thông tin từ file DxDiag.txt cho Laptop/Desktop
- ✅ Nhập tay thông tin cho các thiết bị khác
- ✅ Xem lịch sử thiết bị (sửa chữa, thay thế, di chuyển, thanh lý)
- ✅ Quản lý theo công ty
- ✅ Giao diện hiện đại, thân thiện

## Cài đặt

1. Cài đặt Python 3.8+ và pip

2. Cài đặt các package cần thiết:
```bash
pip install -r requirements.txt
```

3. Chạy migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Tạo superuser để truy cập admin:
```bash
python manage.py createsuperuser
```

5. Tạo dữ liệu mẫu (3 công ty):
```bash
python manage.py shell
```

Trong shell, chạy:
```python
from equipment.models import Company

Company.objects.create(name="Saigonbooks", code="SGB")
Company.objects.create(name="Zenbooks", code="ZNB")
Company.objects.create(name="Pegaholdings", code="PEG")
```

6. Chạy server:
```bash
python manage.py runserver
```

7. Truy cập:
- Trang chủ: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Sử dụng

### Thêm thiết bị mới

1. Vào menu "Thêm thiết bị"
2. Chọn công ty và loại thiết bị
3. Nếu là Laptop/Desktop:
   - Upload file DxDiag.txt để tự động điền thông tin
   - Hoặc nhập tay các thông tin
4. Nếu là thiết bị khác (Router, Switch, ...):
   - Nhập tay các thông tin cần thiết
5. Điền thông số kỹ thuật (nếu có)
6. Lưu

### Xem lịch sử thiết bị

1. Vào trang chi tiết thiết bị
2. Click "Xem lịch sử"
3. Xem bảng lịch sử theo mẫu (STT, Ngày, Nội dung chi tiết, Ký tên)
4. Có thể thêm, sửa, xóa lịch sử

### Thêm lịch sử

1. Vào trang lịch sử thiết bị
2. Click "Thêm lịch sử"
3. Điền thông tin:
   - Ngày
   - Loại hành động (Sửa chữa, Thay thế, Di chuyển, Thanh lý, ...)
   - Nội dung chi tiết
   - Ký tên
4. Lưu

## Cấu trúc dự án

```
quanlycongcudungcu/
├── equipment_management/    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── equipment/               # Equipment app
│   ├── models.py           # Models: Company, Equipment, EquipmentHistory
│   ├── views.py            # Views
│   ├── forms.py            # Forms
│   ├── parser.py           # DxDiag parser
│   ├── admin.py            # Admin interface
│   └── templates/          # HTML templates
├── manage.py
├── requirements.txt
└── README.md
```

## Models

- **Company**: Công ty (Saigonbooks, Zenbooks, Pegaholdings)
- **Equipment**: Thiết bị (Laptop, Desktop, Router, Switch, ...)
- **EquipmentHistory**: Lịch sử thiết bị (sửa chữa, thay thế, di chuyển, thanh lý)

## File DxDiag.txt

File DxDiag.txt được tạo từ Windows bằng lệnh:
```
dxdiag /t dxdiag.txt
```

Hệ thống sẽ tự động parse và trích xuất:
- Tên máy
- Hệ điều hành
- Nhà sản xuất
- Model
- Bộ xử lý
- Bộ nhớ
- Card đồ họa
- Các thông số kỹ thuật khác

