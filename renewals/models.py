from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta


class RenewalType(models.Model):
    """Loại dịch vụ cần gia hạn"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên loại")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    order = models.IntegerField(default=0, verbose_name="Thứ tự sắp xếp")
    
    class Meta:
        verbose_name = "Loại dịch vụ"
        verbose_name_plural = "Loại dịch vụ"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Renewal(models.Model):
    """Thông tin gia hạn các dịch vụ"""
    
    STATUS_CHOICES = [
        ('active', 'Đang hoạt động'),
        ('expired', 'Đã hết hạn'),
        ('cancelled', 'Đã hủy'),
    ]
    
    renewal_type = models.ForeignKey(
        RenewalType,
        on_delete=models.CASCADE,
        verbose_name="Loại dịch vụ"
    )
    name = models.CharField(max_length=200, verbose_name="Tên dịch vụ")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    
    # Thông tin gia hạn
    start_date = models.DateField(verbose_name="Ngày bắt đầu")
    expiry_date = models.DateField(verbose_name="Ngày hết hạn")
    renewal_period = models.IntegerField(
        default=12,
        verbose_name="Chu kỳ gia hạn (tháng)",
        help_text="Số tháng gia hạn mỗi lần"
    )
    cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Chi phí",
        help_text="Chi phí gia hạn (VND)"
    )
    
    # Thông tin nhà cung cấp
    provider = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nhà cung cấp"
    )
    provider_contact = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Liên hệ nhà cung cấp"
    )
    
    # Thông tin quản lý
    company = models.ForeignKey(
        'equipment.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Công ty"
    )
    responsible_person = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='renewals_responsible',
        verbose_name="Người phụ trách"
    )
    
    # Trạng thái
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Trạng thái"
    )
    
    # Thông tin bổ sung
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    auto_renewal = models.BooleanField(
        default=False,
        verbose_name="Tự động gia hạn"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='renewals_created',
        verbose_name="Người tạo"
    )
    
    class Meta:
        verbose_name = "Gia hạn dịch vụ"
        verbose_name_plural = "Gia hạn dịch vụ"
        ordering = ['expiry_date', 'renewal_type']
    
    def __str__(self):
        return f"{self.name} ({self.renewal_type.name})"
    
    def get_absolute_url(self):
        return reverse('renewals:renewal_detail', kwargs={'pk': self.pk})
    
    @property
    def is_expired(self):
        """Kiểm tra xem đã hết hạn chưa"""
        return self.expiry_date < timezone.now().date()
    
    @property
    def days_until_expiry(self):
        """Số ngày còn lại đến khi hết hạn"""
        delta = self.expiry_date - timezone.now().date()
        return delta.days
    
    @property
    def is_expiring_soon(self):
        """Kiểm tra xem có sắp hết hạn không (trong vòng 30 ngày)"""
        return 0 <= self.days_until_expiry <= 30
    
    @property
    def is_critical(self):
        """Kiểm tra xem có nguy cơ cao không (trong vòng 7 ngày)"""
        return 0 <= self.days_until_expiry <= 7
    
    def renew(self, new_expiry_date=None):
        """Gia hạn dịch vụ"""
        if new_expiry_date is None:
            # Tự động tính ngày hết hạn mới dựa trên chu kỳ
            if self.expiry_date:
                new_expiry_date = self.expiry_date + timedelta(days=30 * self.renewal_period)
            else:
                new_expiry_date = timezone.now().date() + timedelta(days=30 * self.renewal_period)
        
        self.expiry_date = new_expiry_date
        self.status = 'active'
        self.save()


class RenewalHistory(models.Model):
    """Lịch sử gia hạn"""
    renewal = models.ForeignKey(
        Renewal,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name="Dịch vụ"
    )
    renewal_date = models.DateField(verbose_name="Ngày gia hạn")
    old_expiry_date = models.DateField(verbose_name="Ngày hết hạn cũ")
    new_expiry_date = models.DateField(verbose_name="Ngày hết hạn mới")
    cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Chi phí gia hạn"
    )
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    renewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Người gia hạn"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    class Meta:
        verbose_name = "Lịch sử gia hạn"
        verbose_name_plural = "Lịch sử gia hạn"
        ordering = ['-renewal_date', '-created_at']
    
    def __str__(self):
        return f"{self.renewal.name} - {self.renewal_date}"
