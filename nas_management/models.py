from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class NASConfig(models.Model):
    """Cấu hình kết nối NAS Synology"""
    name = models.CharField(max_length=200, verbose_name="Tên NAS", unique=True)
    host = models.CharField(max_length=255, verbose_name="Địa chỉ IP/Domain")
    port = models.IntegerField(default=5000, verbose_name="Port")
    username = models.CharField(max_length=100, verbose_name="Username")
    password = models.CharField(max_length=255, verbose_name="Password")
    use_https = models.BooleanField(default=True, verbose_name="Sử dụng HTTPS")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cấu hình NAS"
        verbose_name_plural = "Cấu hình NAS"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.host})"

    def get_api_url(self):
        """Lấy URL API"""
        # Loại bỏ protocol nếu có trong host
        host = self.host.strip()
        if host.startswith('http://'):
            host = host[7:]
        elif host.startswith('https://'):
            host = host[8:]
        
        # Loại bỏ port nếu có trong host
        if ':' in host:
            host = host.split(':')[0]
        
        # Tạo URL
        protocol = 'https' if self.use_https else 'http'
        return f"{protocol}://{host}:{self.port}"


class LoginHistory(models.Model):
    """Lịch sử đăng nhập NAS"""
    nas = models.ForeignKey(NASConfig, on_delete=models.CASCADE, related_name='login_history', verbose_name="NAS")
    username = models.CharField(max_length=100, verbose_name="Username")
    ip_address = models.GenericIPAddressField(verbose_name="IP Address")
    login_time = models.DateTimeField(verbose_name="Thời gian đăng nhập")
    logout_time = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian đăng xuất")
    is_success = models.BooleanField(default=True, verbose_name="Đăng nhập thành công")
    failure_reason = models.CharField(max_length=500, blank=True, verbose_name="Lý do thất bại")
    user_agent = models.CharField(max_length=500, blank=True, verbose_name="User Agent")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lịch sử đăng nhập"
        verbose_name_plural = "Lịch sử đăng nhập"
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['-login_time']),
            models.Index(fields=['username', '-login_time']),
            models.Index(fields=['is_success', '-login_time']),
        ]

    def __str__(self):
        status = "Thành công" if self.is_success else "Thất bại"
        return f"{self.username} - {self.ip_address} - {status} - {self.login_time.strftime('%d/%m/%Y %H:%M')}"


class SystemStats(models.Model):
    """Thống kê hệ thống NAS (CPU, RAM, Disk)"""
    nas = models.ForeignKey(NASConfig, on_delete=models.CASCADE, related_name='system_stats', verbose_name="NAS")
    cpu_usage = models.FloatField(verbose_name="CPU Usage (%)")
    memory_usage = models.FloatField(verbose_name="Memory Usage (%)")
    memory_total = models.BigIntegerField(verbose_name="Total Memory (bytes)")
    memory_used = models.BigIntegerField(verbose_name="Used Memory (bytes)")
    disk_usage = models.JSONField(default=dict, verbose_name="Disk Usage")
    network_stats = models.JSONField(default=dict, blank=True, verbose_name="Network Statistics")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Thời gian")

    class Meta:
        verbose_name = "Thống kê hệ thống"
        verbose_name_plural = "Thống kê hệ thống"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['nas', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.nas.name} - CPU: {self.cpu_usage}% - RAM: {self.memory_usage}% - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class NASLog(models.Model):
    """Log của NAS"""
    LOG_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    LOG_TYPE_CHOICES = [
        ('syslog', 'System Log'),
        ('connectlog', 'Connection Log'),
        ('filexferlog', 'File Transfer Log'),
    ]
    
    nas = models.ForeignKey(NASConfig, on_delete=models.CASCADE, related_name='logs', verbose_name="NAS")
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES, default='syslog', verbose_name="Loại log")
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default='info', verbose_name="Mức độ")
    category = models.CharField(max_length=100, blank=True, verbose_name="Danh mục")
    message = models.TextField(verbose_name="Nội dung")
    source = models.CharField(max_length=200, blank=True, verbose_name="Nguồn")
    timestamp = models.DateTimeField(verbose_name="Thời gian")
    # Thêm các field cho filexferlog
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    file_path = models.CharField(max_length=1000, blank=True, verbose_name="Đường dẫn file")
    file_size = models.CharField(max_length=100, blank=True, verbose_name="Kích thước file")
    file_name = models.CharField(max_length=500, blank=True, verbose_name="Tên file")
    operation = models.CharField(max_length=50, blank=True, verbose_name="Thao tác")  # Read, Write, Delete, Create
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log NAS"
        verbose_name_plural = "Log NAS"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['nas', '-timestamp']),
            models.Index(fields=['level', '-timestamp']),
            models.Index(fields=['log_type', '-timestamp']),
            models.Index(fields=['nas', 'log_type', '-timestamp']),
        ]
        unique_together = [['nas', 'log_type', 'timestamp', 'message']]

    def __str__(self):
        return f"{self.nas.name} - {self.level} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class FileOperation(models.Model):
    """Lịch sử thao tác file/folder"""
    OPERATION_CHOICES = [
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('delete', 'Delete'),
        ('create_folder', 'Create Folder'),
        ('rename', 'Rename'),
        ('move', 'Move'),
        ('copy', 'Copy'),
    ]
    
    nas = models.ForeignKey(NASConfig, on_delete=models.CASCADE, related_name='file_operations', verbose_name="NAS")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Người thực hiện")
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES, verbose_name="Thao tác")
    file_path = models.CharField(max_length=1000, verbose_name="Đường dẫn file")
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name="Kích thước (bytes)")
    is_success = models.BooleanField(default=True, verbose_name="Thành công")
    error_message = models.TextField(blank=True, verbose_name="Lỗi")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Thời gian")

    class Meta:
        verbose_name = "Thao tác file"
        verbose_name_plural = "Thao tác file"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['nas', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['operation', '-timestamp']),
        ]

    def __str__(self):
        status = "Thành công" if self.is_success else "Thất bại"
        return f"{self.operation} - {self.file_path} - {status}"
