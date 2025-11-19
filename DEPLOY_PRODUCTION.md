# Hướng dẫn Deploy lên Production - ccdc.saigonbooks.vn

Hướng dẫn deploy ứng dụng Quản lý Thiết bị IT lên production server với domain **https://ccdc.saigonbooks.vn/**

## Bước 1: Chuẩn bị trên Server

### 1.1. SSH vào server

```bash
ssh user@your-server-ip
```

### 1.2. Cài đặt dependencies

```bash
# Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Cài đặt Python và dependencies
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential libpq-dev libldap2-dev libsasl2-dev

# Cài đặt PostgreSQL (nếu chưa có)
sudo apt install -y postgresql postgresql-contrib
```

## Bước 2: Upload Code lên Server

### 2.1. Upload code (nếu chưa có)

```bash
# Từ máy local, upload code lên server
scp -r /path/to/quanlycongcudungcu user@server:/home/user/

# Hoặc dùng Git
cd /home/user
git clone your-repo-url quanlycongcudungcu
cd quanlycongcudungcu
```

### 2.2. Tạo virtual environment

```bash
cd /home/user/quanlycongcudungcu
python3 -m venv venv
source venv/bin/activate
```

### 2.3. Cài đặt Python packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Bước 3: Cấu hình Database

### 3.1. Tạo PostgreSQL database

```bash
sudo -u postgres psql
```

Trong PostgreSQL shell:

```sql
CREATE DATABASE equipment_db;
CREATE USER equipment_user WITH PASSWORD 'your_strong_password';
ALTER ROLE equipment_user SET client_encoding TO 'utf8';
ALTER ROLE equipment_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE equipment_user SET timezone TO 'Asia/Ho_Chi_Minh';
GRANT ALL PRIVILEGES ON DATABASE equipment_db TO equipment_user;
\q
```

## Bước 4: Cấu hình Environment Variables

### 4.1. Tạo file .env

```bash
cd /home/user/quanlycongcudungcu
nano .env
```

Nội dung file `.env`:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=False
ALLOWED_HOSTS=ccdc.saigonbooks.vn,www.ccdc.saigonbooks.vn

# Database
DB_NAME=equipment_db
DB_USER=equipment_user
DB_PASSWORD=your_strong_password_here
DB_HOST=localhost
DB_PORT=5432

# SSL
SECURE_SSL_REDIRECT=True

# LDAP Settings
LDAP_SERVER=192.168.104.80
LDAP_DOMAIN=pegaholdings.local
LDAP_PORT=389
LDAP_USE_SSL=False
LDAP_BASE_DN=DC=pegaholdings,DC=local
LDAP_SEARCH_DN=CN=Users,DC=pegaholdings,DC=local

# LDAP Search User (để sync users)
LDAP_SEARCH_USER=p.huy.nn
LDAP_SEARCH_USER_PASSWORD=Pega@2025

# Email Settings (nếu cần)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@ccdc.saigonbooks.vn
```

### 4.2. Generate SECRET_KEY mới

```bash
python manage.py shell
```

Trong shell:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Copy secret key và paste vào `.env`

## Bước 5: Chạy Migrations và Setup

### 5.1. Chạy migrations

```bash
cd /home/user/quanlycongcudungcu
source venv/bin/activate
python manage.py migrate --settings=equipment_management.settings_production
```

### 5.2. Sync users từ LDAP

```bash
python manage.py sync_ldap_users --settings=equipment_management.settings_production
```

Lệnh này sẽ sync tất cả 139 users từ LDAP lên database.

### 5.3. Tạo superuser (nếu cần)

```bash
python manage.py createsuperuser --settings=equipment_management.settings_production
```

### 5.4. Collect static files

```bash
python manage.py collectstatic --noinput --settings=equipment_management.settings_production
```

## Bước 6: Cấu hình Gunicorn

### 6.1. Test Gunicorn

```bash
gunicorn --config gunicorn_config.py equipment_management.wsgi:application --settings=equipment_management.settings_production
```

### 6.2. Tạo Systemd Service

```bash
sudo nano /etc/systemd/system/equipment_management.service
```

Nội dung:

```ini
[Unit]
Description=Equipment Management Gunicorn daemon
After=network.target

[Service]
User=user
Group=user
WorkingDirectory=/home/user/quanlycongcudungcu
Environment="PATH=/home/user/quanlycongcudungcu/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=equipment_management.settings_production"
ExecStart=/home/user/quanlycongcudungcu/venv/bin/gunicorn \
    --config /home/user/quanlycongcudungcu/gunicorn_config.py \
    equipment_management.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

### 6.3. Khởi động service

```bash
sudo systemctl daemon-reload
sudo systemctl start equipment_management
sudo systemctl enable equipment_management
sudo systemctl status equipment_management
```

## Bước 7: Cấu hình Nginx

### 7.1. Tạo Nginx config

```bash
sudo nano /etc/nginx/sites-available/ccdc.saigonbooks.vn
```

Nội dung:

```nginx
server {
    listen 80;
    server_name ccdc.saigonbooks.vn www.ccdc.saigonbooks.vn;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ccdc.saigonbooks.vn www.ccdc.saigonbooks.vn;

    # SSL certificates (sẽ được cấu hình bởi Certbot)
    ssl_certificate /etc/letsencrypt/live/ccdc.saigonbooks.vn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ccdc.saigonbooks.vn/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static/ {
        alias /home/user/quanlycongcudungcu/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/user/quanlycongcudungcu/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    client_max_body_size 100M;
}
```

### 7.2. Enable site

```bash
sudo ln -s /etc/nginx/sites-available/ccdc.saigonbooks.vn /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Bước 8: Cài đặt SSL Certificate

### 8.1. Cài đặt Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 8.2. Cấu hình SSL

```bash
sudo certbot --nginx -d ccdc.saigonbooks.vn -d www.ccdc.saigonbooks.vn
```

Certbot sẽ tự động cấu hình SSL và cập nhật Nginx config.

### 8.3. Test auto-renewal

```bash
sudo certbot renew --dry-run
```

## Bước 9: Kiểm tra

### 9.1. Kiểm tra services

```bash
sudo systemctl status equipment_management
sudo systemctl status nginx
sudo systemctl status postgresql
```

### 9.2. Kiểm tra logs

```bash
# Django logs
tail -f /home/user/quanlycongcudungcu/logs/django.log

# Gunicorn logs
sudo journalctl -u equipment_management -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 9.3. Test website

Truy cập: https://ccdc.saigonbooks.vn/

## Bước 10: Sync Users từ LDAP (Sau khi deploy)

Sau khi deploy xong, sync tất cả users từ LDAP:

```bash
cd /home/user/quanlycongcudungcu
source venv/bin/activate
python manage.py sync_ldap_users --settings=equipment_management.settings_production
```

Lệnh này sẽ:
- Kết nối LDAP server (192.168.104.80)
- Lấy tất cả users từ LDAP
- Tạo/cập nhật users trong Django database
- Tất cả users có thể đăng nhập với username/password LDAP

## Cập nhật Code sau này

```bash
cd /home/user/quanlycongcudungcu
source venv/bin/activate
git pull  # Nếu dùng Git
pip install -r requirements.txt
python manage.py migrate --settings=equipment_management.settings_production
python manage.py collectstatic --noinput --settings=equipment_management.settings_production
sudo systemctl restart equipment_management
```

## Troubleshooting

### Lỗi: "Can't connect to LDAP server"

- Kiểm tra server có thể kết nối đến 192.168.104.80:389
- Kiểm tra firewall không chặn port 389
- Kiểm tra LDAP_SEARCH_USER và LDAP_SEARCH_USER_PASSWORD trong .env

### Lỗi: "Permission denied"

```bash
sudo chown -R user:user /home/user/quanlycongcudungcu
sudo chmod -R 755 /home/user/quanlycongcudungcu
```

### Restart services

```bash
sudo systemctl restart equipment_management
sudo systemctl restart nginx
```

## Lưu ý quan trọng

1. **SECRET_KEY**: Phải generate mới cho production, không dùng key từ development
2. **DEBUG**: Phải set `False` trong production
3. **ALLOWED_HOSTS**: Phải bao gồm domain `ccdc.saigonbooks.vn`
4. **LDAP**: Đảm bảo server có thể kết nối đến LDAP server (192.168.104.80)
5. **SSL**: Sử dụng HTTPS trong production
6. **Backup**: Nên setup backup định kỳ cho database

## Backup Database

Tạo script backup:

```bash
nano /home/user/quanlycongcudungcu/backup.sh
```

Nội dung:

```bash
#!/bin/bash
BACKUP_DIR="/home/user/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U equipment_user equipment_db > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/user/quanlycongcudungcu/media/

# Xóa backup cũ hơn 7 ngày
find $BACKUP_DIR -type f -mtime +7 -delete
```

Thêm vào crontab:

```bash
crontab -e
```

Thêm dòng:

```
0 2 * * * /home/user/quanlycongcudungcu/backup.sh
```

