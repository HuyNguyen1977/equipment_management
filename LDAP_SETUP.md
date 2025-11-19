# Hướng dẫn Setup LDAP Authentication

Hệ thống đã được cấu hình để sử dụng LDAP authentication với domain **pegaholdings.local**.

## Cấu hình

### LDAP Server
- **Server**: 192.168.104.80
- **Domain**: pegaholdings.local
- **Port**: 389 (LDAP) hoặc 636 (LDAPS)
- **Base DN**: DC=pegaholdings,DC=local

## Cài đặt

### 1. Cài đặt python-ldap

```bash
pip install python-ldap
```

**Lưu ý trên Windows:**
- Cần cài đặt OpenLDAP libraries trước
- Hoặc sử dụng pre-built wheel: `pip install python-ldap` (nếu có sẵn)
- Nếu gặp lỗi, thử: `pip install python-ldap --global-option=build_ext --global-option="-IC:\path\to\openldap\include"`

**Trên Linux:**
```bash
sudo apt-get install libldap2-dev libsasl2-dev
pip install python-ldap
```

### 2. Cấu hình trong settings.py

Cấu hình đã được thêm tự động vào `equipment_management/settings.py`:

```python
# LDAP Authentication Settings
LDAP_SERVER = '192.168.104.80'
LDAP_DOMAIN = 'pegaholdings.local'
LDAP_PORT = 389
LDAP_USE_SSL = False
LDAP_BASE_DN = 'DC=pegaholdings,DC=local'
LDAP_SEARCH_DN = 'CN=Users,DC=pegaholdings,DC=local'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'equipment.ldap_backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### 3. Cấu hình tùy chọn (nếu cần)

Nếu LDAP server yêu cầu service account để search users, thêm vào `.env` hoặc `settings.py`:

```python
LDAP_SERVICE_DN = 'CN=ServiceAccount,CN=Users,DC=pegaholdings,DC=local'
LDAP_SERVICE_PASSWORD = 'service_password'
```

## Cách hoạt động

1. **User đăng nhập** với username và password LDAP
2. **LDAP Backend** tìm user trong LDAP bằng `sAMAccountName`
3. **Xác thực** bằng cách bind với user DN và password
4. **Tự động tạo Django User** nếu chưa tồn tại
5. **Cập nhật thông tin** từ LDAP (email, first_name, last_name)

## Test LDAP Connection

### Test bằng management command:

```bash
python manage.py test_ldap --username your_ldap_username --password your_ldap_password
```

### Test bằng Django shell:

```python
from equipment.ldap_backend import LDAPBackend

backend = LDAPBackend()
user = backend.authenticate(None, username='your_username', password='your_password')

if user:
    print(f"Success! User: {user.username}, Email: {user.email}")
else:
    print("Authentication failed")
```

## Sử dụng

### Đăng nhập qua Web

1. Vào trang login: `http://localhost:8000/login/`
2. Nhập **username LDAP** (không cần domain, ví dụ: `john.doe` thay vì `john.doe@pegaholdings.local`)
3. Nhập **password LDAP**
4. Click "Đăng nhập"

### Đăng nhập qua API

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_ldap_username", "password": "your_ldap_password"}'
```

## Troubleshooting

### Lỗi: "ModuleNotFoundError: No module named 'ldap'"

**Giải pháp:**
```bash
pip install python-ldap
```

### Lỗi: "Can't contact LDAP server"

**Kiểm tra:**
1. LDAP server có đang chạy không?
2. Firewall có chặn port 389/636 không?
3. IP address đúng chưa? (192.168.104.80)

**Test kết nối:**
```bash
# Trên Linux/Mac
ldapsearch -x -H ldap://192.168.104.80 -b "DC=pegaholdings,DC=local"

# Hoặc dùng telnet
telnet 192.168.104.80 389
```

### Lỗi: "Invalid credentials"

**Kiểm tra:**
1. Username và password đúng chưa?
2. User có tồn tại trong LDAP không?
3. User có bị disable không?

### Lỗi: "Anonymous bind not allowed"

**Giải pháp:**
Cần cấu hình service account:
```python
LDAP_SERVICE_DN = 'CN=ServiceAccount,CN=Users,DC=pegaholdings,DC=local'
LDAP_SERVICE_PASSWORD = 'service_password'
```

### User được tạo nhưng không có quyền

**Giải pháp:**
- User mới tạo từ LDAP mặc định không phải staff/superuser
- Cần set quyền thủ công hoặc dựa vào group membership trong LDAP

## Nâng cao

### Tự động set quyền dựa trên LDAP Group

Có thể mở rộng `LDAPBackend` để:
1. Lấy danh sách groups của user từ LDAP
2. Tự động set `is_staff` hoặc `is_superuser` dựa trên group membership

### Sync thông tin định kỳ

Có thể tạo management command để sync thông tin user từ LDAP định kỳ.

## Lưu ý

- **Password không được lưu**: Django User được tạo với `set_unusable_password()`, chỉ xác thực qua LDAP
- **Fallback**: Nếu LDAP không hoạt động, hệ thống vẫn có thể dùng Django default authentication
- **Security**: Trong production, nên dùng LDAPS (port 636) thay vì LDAP (port 389)

