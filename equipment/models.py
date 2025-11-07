from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from decimal import Decimal


class Company(models.Model):
    """Công ty"""
    name = models.CharField(max_length=200, verbose_name="Tên công ty")
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã công ty")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Công ty"
        verbose_name_plural = "Công ty"
        ordering = ['name']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """Thiết bị"""
    EQUIPMENT_TYPES = [
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('router', 'Router'),
        ('switch', 'Switch'),
        ('printer', 'Máy in'),
        ('scanner', 'Máy quét'),
        ('other', 'Khác'),
    ]
    
    REGIONS = [
        ('MN', 'Miền Nam'),
        ('MT', 'Miền Trung'),
        ('MB', 'Miền Bắc'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Công ty")
    region = models.CharField(max_length=2, choices=REGIONS, verbose_name="Miền", default='MN')
    name = models.CharField(max_length=200, verbose_name="Tên thiết bị")
    code = models.CharField(max_length=100, unique=True, verbose_name="Ký hiệu mã")
    equipment_type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES, verbose_name="Loại thiết bị")
    commission_date = models.DateField(null=True, blank=True, verbose_name="Thời điểm đưa vào sử dụng")
    
    # Thông tin từ DxDiag (cho laptop/desktop)
    machine_name = models.CharField(max_length=200, blank=True, verbose_name="Tên máy")
    operating_system = models.CharField(max_length=200, blank=True, verbose_name="Hệ điều hành")
    system_manufacturer = models.CharField(max_length=200, blank=True, verbose_name="Nhà sản xuất")
    system_model = models.CharField(max_length=200, blank=True, verbose_name="Model")
    processor = models.CharField(max_length=200, blank=True, verbose_name="Bộ xử lý")
    memory = models.CharField(max_length=100, blank=True, verbose_name="Bộ nhớ")
    graphics_card = models.CharField(max_length=200, blank=True, verbose_name="Card đồ họa")
    monitor_name = models.CharField(max_length=200, blank=True, verbose_name="Monitor Name")
    monitor_model = models.CharField(max_length=200, blank=True, verbose_name="Monitor Model")
    
    # Thông số kỹ thuật (JSON field hoặc TextField)
    technical_specs = models.JSONField(default=dict, blank=True, verbose_name="Thông số kỹ thuật")
    
    # Tài liệu hướng dẫn
    documentation = models.TextField(blank=True, verbose_name="Tài liệu hướng dẫn kèm theo")
    
    # File DxDiag nếu có
    dxdiag_file = models.FileField(upload_to='dxdiag/', blank=True, null=True, verbose_name="File DxDiag")
    
    # Người đang sử dụng
    current_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='equipment_using',
        verbose_name="Người đang sử dụng"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    class Meta:
        verbose_name = "Thiết bị"
        verbose_name_plural = "Thiết bị"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"


class EquipmentHistory(models.Model):
    """Lịch sử thiết bị - sửa chữa, thay thế, di chuyển, thanh lý"""
    ACTION_TYPES = [
        ('repair', 'Sửa chữa'),
        ('replacement', 'Thay thế'),
        ('movement', 'Di chuyển'),
        ('liquidation', 'Thanh lý'),
        ('maintenance', 'Bảo trì'),
        ('upgrade', 'Nâng cấp'),
        ('user_assignment', 'Giao máy cho người dùng'),
        ('user_return', 'Trả máy'),
        ('other', 'Khác'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='histories', verbose_name="Thiết bị")
    action_date = models.DateField(verbose_name="Ngày")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name="Loại hành động")
    description = models.TextField(verbose_name="Nội dung chi tiết")
    signed_by = models.CharField(max_length=200, verbose_name="Ký tên")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Lịch sử thiết bị"
        verbose_name_plural = "Lịch sử thiết bị"
        ordering = ['-action_date', '-created_at']

    def __str__(self):
        return f"{self.equipment.name} - {self.get_action_type_display()} - {self.action_date}"

