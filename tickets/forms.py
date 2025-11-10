from django import forms
from django.contrib.auth.models import User
from .models import Ticket, TicketComment, TicketAttachment, Company, Department, TicketCategory


class TicketForm(forms.ModelForm):
    """Form tạo ticket từ webform"""
    requester_name = forms.CharField(
        max_length=200,
        label="Họ và tên",
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Nhập họ và tên của bạn'
        })
    )
    requester_email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'input',
            'placeholder': 'email@example.com'
        })
    )
    requester_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Số điện thoại",
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Số điện thoại (tùy chọn)'
        })
    )
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        label="Công ty",
        widget=forms.Select(attrs={'class': 'select is-fullwidth'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Phòng ban",
        widget=forms.Select(attrs={'class': 'select is-fullwidth'})
    )
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.filter(parent__isnull=False),
        required=False,
        label="Loại yêu cầu",
        widget=forms.Select(attrs={'class': 'select is-fullwidth'})
    )
    priority = forms.ChoiceField(
        choices=Ticket.PRIORITY_CHOICES,
        label="Mức độ ưu tiên",
        widget=forms.Select(attrs={'class': 'select is-fullwidth'}),
        initial='medium'
    )
    title = forms.CharField(
        max_length=500,
        label="Tiêu đề",
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Tóm tắt ngắn gọn vấn đề của bạn'
        })
    )
    description = forms.CharField(
        label="Mô tả chi tiết",
        widget=forms.Textarea(attrs={
            'class': 'textarea',
            'rows': 6,
            'placeholder': 'Mô tả chi tiết vấn đề bạn gặp phải...'
        })
    )
    attachment = forms.FileField(
        required=False,
        label="File đính kèm (nếu có)",
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip,.rar'
        })
    )

    class Meta:
        model = Ticket
        fields = [
            'requester_name', 'requester_email', 'requester_phone',
            'company', 'department', 'category', 'priority',
            'title', 'description'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Chỉ hiển thị các category con (không hiển thị category cha)
        self.fields['category'].queryset = TicketCategory.objects.filter(parent__isnull=False)
        
        # Sắp xếp theo tên
        self.fields['company'].queryset = Company.objects.all().order_by('name')
        self.fields['department'].queryset = Department.objects.all().order_by('name')

    def save(self, commit=True):
        ticket = super().save(commit=False)
        # Tìm hoặc tạo user từ email
        email = self.cleaned_data['requester_email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Tạo user mới nếu chưa có
            username = email.split('@')[0]
            # Đảm bảo username là duy nhất
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=self.cleaned_data['requester_name'].split()[0] if self.cleaned_data['requester_name'] else '',
                last_name=' '.join(self.cleaned_data['requester_name'].split()[1:]) if len(self.cleaned_data['requester_name'].split()) > 1 else '',
                password='Pega@2025'  # Password mặc định
            )
        
        ticket.requester = user
        ticket.status = 'new'
        
        if commit:
            ticket.save()
        return ticket


class TicketUpdateForm(forms.ModelForm):
    """Form cập nhật ticket (cho IT)"""
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        label="Phân công cho",
        widget=forms.Select(attrs={'class': 'select is-fullwidth'})
    )
    status = forms.ChoiceField(
        choices=Ticket.STATUS_CHOICES,
        label="Trạng thái",
        widget=forms.Select(attrs={'class': 'select is-fullwidth'})
    )
    priority = forms.ChoiceField(
        choices=Ticket.PRIORITY_CHOICES,
        label="Mức độ ưu tiên",
        widget=forms.Select(attrs={'class': 'select is-fullwidth'})
    )
    resolution = forms.CharField(
        required=False,
        label="Kết quả xử lý",
        widget=forms.Textarea(attrs={
            'class': 'textarea',
            'rows': 4,
            'placeholder': 'Mô tả cách xử lý và kết quả...'
        })
    )

    class Meta:
        model = Ticket
        fields = ['assigned_to', 'status', 'priority', 'resolution']


class TicketCommentForm(forms.ModelForm):
    """Form thêm bình luận"""
    content = forms.CharField(
        label="Nội dung",
        widget=forms.Textarea(attrs={
            'class': 'textarea',
            'rows': 3,
            'placeholder': 'Nhập bình luận hoặc ghi chú...'
        })
    )
    is_internal = forms.BooleanField(
        required=False,
        label="Ghi chú nội bộ",
        help_text="Chỉ nhân viên IT mới thấy được",
        widget=forms.CheckboxInput(attrs={'class': 'checkbox'})
    )

    class Meta:
        model = TicketComment
        fields = ['content', 'is_internal']


class TicketAttachmentForm(forms.ModelForm):
    """Form upload file đính kèm"""
    file = forms.FileField(
        label="Chọn file",
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip,.rar'
        })
    )

    class Meta:
        model = TicketAttachment
        fields = ['file']

    def save(self, commit=True):
        attachment = super().save(commit=False)
        if attachment.file:
            attachment.filename = attachment.file.name
        if commit:
            attachment.save()
        return attachment

