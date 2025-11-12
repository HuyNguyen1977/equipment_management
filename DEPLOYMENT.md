# Hướng dẫn Deploy Django lên Ubuntu Server

Hướng dẫn chi tiết để deploy ứng dụng Quản lý Thiết bị IT lên Ubuntu server với Gunicorn, Nginx và PostgreSQL.

## Yêu cầu

- Ubuntu Server 20.04 LTS hoặc mới hơn
- Quyền root hoặc sudo
- Domain name (tùy chọn, có thể dùng IP)
- Tối thiểu 1GB RAM, 10GB disk space

## Bước 1: Chuẩn bị Server

### 1.1. Cập nhật hệ thống

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2. Tạo user mới (khuyến nghị)

```bash
sudo adduser django
sudo usermod -aG sudo django
su - django
```

## Bước 2: Cài đặt Python và Dependencies

### 2.1. Cài đặt Python và pip

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential libpq-dev
```

### 2.2. Cài đặt PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2.3. Tạo database và user

```bash
sudo -u postgres psql
```

Trong PostgreSQL shell:

```sql
CREATE DATABASE equipment_db;
CREATE USER equipment_user WITH PASSWORD 'your_strong_password_here';
ALTER ROLE equipment_user SET client_encoding TO 'utf8';
ALTER ROLE equipment_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE equipment_user SET timezone TO 'Asia/Ho_Chi_Minh';
GRANT ALL PRIVILEGES ON DATABASE equipment_db TO equipment_user;
\q
```

## Bước 3: Deploy Application

### 3.1. Clone hoặc upload code lên server

```bash
# Nếu dùng Git
cd /home/django
git clone https://github.com/HuyNguyen1977/equipment_management.git
cd equipment_management

# Hoặc upload code qua SCP/SFTP
```

### 3.2. Tạo virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.3. Cài đặt dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 3.4. Cập nhật requirements.txt

Đảm bảo `requirements.txt` có:

```
Django>=4.2.0
openpyxl
gunicorn
psycopg2-binary
```

## Bước 4: Cấu hình Django cho Production

### 4.1. Tạo file settings cho production

Tạo file `equipment_management/settings_production.py`:

```python
from .settings import *
import os
from pathlib import Path

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'your-server-ip']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'equipment_db'),
        'USER': os.environ.get('DB_USER', 'equipment_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 4.2. Tạo thư mục logs

```bash
mkdir -p logs
```

### 4.3. Tạo file .env (khuyến nghị)

Tạo file `.env` trong thư mục project:

```bash
nano .env
```

Nội dung:

```
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=False
DB_NAME=equipment_db
DB_USER=equipment_user
DB_PASSWORD=your_strong_password_here
DB_HOST=localhost
DB_PORT=5432
```

### 4.4. Cập nhật settings.py để đọc từ .env

Cài đặt python-decouple:

```bash
pip install python-decouple
```

Cập nhật `settings.py`:

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY', default='django-insecure-equipment-management-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
```

### 4.5. Chạy migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4.6. Tạo superuser

```bash
python manage.py createsuperuser
```

### 4.7. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 4.8. Tạo dữ liệu ban đầu (nếu cần)

```bash
python manage.py init_ticket_data  # Nếu có command này
```

## Bước 5: Cấu hình Gunicorn

### 5.1. Tạo file gunicorn config

Tạo file `gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
```

### 5.2. Test Gunicorn

```bash
gunicorn --config gunicorn_config.py equipment_management.wsgi:application
```

## Bước 6: Cấu hình Systemd Service

### 6.1. Tạo service file

```bash
sudo nano /etc/systemd/system/equipment_management.service
```

Nội dung:

```ini
[Unit]
Description=Equipment Management Gunicorn daemon
After=network.target

[Service]
User=django
Group=django
WorkingDirectory=/home/django/equipment_management
Environment="PATH=/home/django/equipment_management/venv/bin"
ExecStart=/home/django/equipment_management/venv/bin/gunicorn \
    --config /home/django/equipment_management/gunicorn_config.py \
    equipment_management.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

### 6.2. Khởi động service

```bash
sudo systemctl daemon-reload
sudo systemctl start equipment_management
sudo systemctl enable equipment_management
sudo systemctl status equipment_management
```

## Bước 7: Cấu hình Nginx

### 7.1. Cài đặt Nginx

```bash
sudo apt install -y nginx
```

### 7.2. Tạo Nginx config

```bash
sudo nano /etc/nginx/sites-available/equipment_management
```

Nội dung:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS (sau khi cài SSL)
    # return 301 https://$server_name$request_uri;

    # Hoặc tạm thời dùng HTTP
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/django/equipment_management/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/django/equipment_management/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    client_max_body_size 100M;
}
```

### 7.3. Enable site

```bash
sudo ln -s /etc/nginx/sites-available/equipment_management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Bước 8: Cấu hình Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## Bước 9: Cài đặt SSL với Let's Encrypt (Tùy chọn)

### 9.1. Cài đặt Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 9.2. Cấu hình SSL

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 9.3. Auto-renewal

```bash
sudo certbot renew --dry-run
```

## Bước 10: Kiểm tra và Monitoring

### 10.1. Kiểm tra logs

```bash
# Django logs
tail -f /home/django/equipment_management/logs/django.log

# Gunicorn logs
sudo journalctl -u equipment_management -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 10.2. Kiểm tra service status

```bash
sudo systemctl status equipment_management
sudo systemctl status nginx
sudo systemctl status postgresql
```

## Bước 11: Backup

### 11.1. Tạo script backup

Tạo file `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/django/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U equipment_user equipment_db > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/django/equipment_management/media/

# Xóa backup cũ hơn 7 ngày
find $BACKUP_DIR -type f -mtime +7 -delete
```

### 11.2. Thêm vào crontab

```bash
crontab -e
```

Thêm dòng:

```
0 2 * * * /home/django/equipment_management/backup.sh
```

## Troubleshooting

### Lỗi Permission denied

```bash
sudo chown -R django:django /home/django/equipment_management
sudo chmod -R 755 /home/django/equipment_management
```

### Lỗi Database connection

Kiểm tra PostgreSQL đang chạy:

```bash
sudo systemctl status postgresql
```

Kiểm tra file `.env` và cấu hình database.

### Lỗi Static files không hiển thị

```bash
python manage.py collectstatic --noinput
sudo chown -R www-data:www-data /home/django/equipment_management/staticfiles
```

### Restart services

```bash
sudo systemctl restart equipment_management
sudo systemctl restart nginx
```

## Cập nhật Code

```bash
cd /home/django/equipment_management
source venv/bin/activate
git pull  # Nếu dùng Git
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart equipment_management
```

## Tài liệu tham khảo

- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)



