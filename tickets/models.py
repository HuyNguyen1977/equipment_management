from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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


class Department(models.Model):
    """Phòng ban"""
    name = models.CharField(max_length=200, verbose_name="Tên phòng ban")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subdepartments',
        verbose_name="Phòng ban cha"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='departments',
        verbose_name="Công ty"
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Thứ tự sắp xếp",
        help_text="Số càng nhỏ càng hiển thị trước. Các item cùng parent sẽ được sắp xếp theo số này."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Phòng ban"
        verbose_name_plural = "Phòng ban"
        ordering = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name


class TicketCategory(models.Model):
    """Loại yêu cầu"""
    name = models.CharField(max_length=200, verbose_name="Tên loại yêu cầu")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Loại cha"
    )
    description = models.TextField(blank=True, verbose_name="Mô tả")
    order = models.IntegerField(
        default=0,
        verbose_name="Thứ tự sắp xếp",
        help_text="Số càng nhỏ càng hiển thị trước. Các item cùng parent sẽ được sắp xếp theo số này."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Loại yêu cầu"
        verbose_name_plural = "Loại yêu cầu"
        ordering = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name


class Ticket(models.Model):
    """Ticket hỗ trợ IT"""
    PRIORITY_CHOICES = [
        ('critical', '🔹 Khẩn cấp (Critical/P1)'),
        ('high', '🔸 Cao (High/P2)'),
        ('medium', '🟡 Trung bình (Medium/P3)'),
        ('low', '⚪ Thấp (Low/P4)'),
    ]

    STATUS_CHOICES = [
        ('new', 'Mới tạo'),
        ('assigned', 'Đã phân công'),
        ('in_progress', 'Đang xử lý'),
        ('resolved', 'Đã xử lý'),
        ('closed', 'Đã đóng'),
        ('cancelled', 'Đã hủy'),
    ]

    # Thông tin cơ bản
    ticket_number = models.CharField(max_length=50, unique=True, verbose_name="Số ticket", editable=False)
    title = models.CharField(max_length=500, verbose_name="Tiêu đề")
    description = models.TextField(verbose_name="Mô tả chi tiết")
    
    # Thông tin người yêu cầu
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requested_tickets',
        verbose_name="Người yêu cầu"
    )
    requester_name = models.CharField(max_length=200, verbose_name="Tên người yêu cầu")
    requester_email = models.EmailField(verbose_name="Email người yêu cầu")
    requester_phone = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    
    # Thông tin công ty và phòng ban
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Công ty"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name="Phòng ban"
    )
    
    # Phân loại và ưu tiên
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name="Loại yêu cầu"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Mức độ ưu tiên"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Trạng thái"
    )
    
    # Thông tin xử lý
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name="Người được phân công"
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời điểm xử lý xong")
    resolution = models.TextField(blank=True, verbose_name="Kết quả xử lý")
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    
    # Đếm số lần lặp lại (để bổ sung loại yêu cầu nếu >3 lần/tháng)
    repeat_count = models.IntegerField(default=0, verbose_name="Số lần lặp lại trong tháng")

    class Meta:
        verbose_name = "Ticket hỗ trợ"
        verbose_name_plural = "Ticket hỗ trợ"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tickets:ticket_detail', kwargs={'ticket_number': self.ticket_number})

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Tạo số ticket tự động: TICKET-YYYYMMDD-XXX
            today = timezone.now().date()
            prefix = f"TICKET-{today.strftime('%Y%m%d')}"
            last_ticket = Ticket.objects.filter(
                ticket_number__startswith=prefix
            ).order_by('-ticket_number').first()
            
            if last_ticket:
                last_num = int(last_ticket.ticket_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.ticket_number = f"{prefix}-{new_num:03d}"
        
        # Tự động cập nhật resolved_at khi status = resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'resolved':
            self.resolved_at = None
        
        super().save(*args, **kwargs)


class TicketComment(models.Model):
    """Bình luận/Ghi chú trên ticket"""
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Ticket"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_comments',
        verbose_name="Người viết"
    )
    content = models.TextField(verbose_name="Nội dung")
    is_internal = models.BooleanField(
        default=False,
        verbose_name="Ghi chú nội bộ",
        help_text="Chỉ IT mới thấy được"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Bình luận ticket"
        verbose_name_plural = "Bình luận ticket"
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.ticket.ticket_number} by {self.author.username}"


class TicketAttachment(models.Model):
    """File đính kèm của ticket"""
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="Ticket"
    )
    file = models.FileField(upload_to='ticket_attachments/%Y/%m/', verbose_name="File")
    filename = models.CharField(max_length=255, verbose_name="Tên file")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_attachments',
        verbose_name="Người upload"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày upload")

    class Meta:
        verbose_name = "File đính kèm"
        verbose_name_plural = "File đính kèm"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} - {self.ticket.ticket_number}"
