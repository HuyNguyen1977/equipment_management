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
    department_parent = forms.ModelChoiceField(
        queryset=Department.objects.filter(parent__isnull=True),
        required=False,
        label="Phòng ban",
        widget=forms.Select(attrs={'class': 'select is-fullwidth', 'id': 'id_department_parent'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),  # Cho phép tất cả để tránh lỗi validation
        required=False,
        label="",
        widget=forms.Select(attrs={'class': 'select is-fullwidth', 'id': 'id_department'})
    )
    category_parent = forms.ModelChoiceField(
        queryset=TicketCategory.objects.filter(parent__isnull=True),
        required=False,
        label="Loại yêu cầu",
        widget=forms.Select(attrs={'class': 'select is-fullwidth', 'id': 'id_category_parent'})
    )
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.all(),  # Cho phép tất cả để tránh lỗi validation
        required=False,
        label="",
        widget=forms.Select(attrs={'class': 'select is-fullwidth', 'id': 'id_category'})
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
            'company', 'department_parent', 'department', 'category_parent', 'category', 'priority',
            'title', 'description'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Sắp xếp theo order và tên
        self.fields['company'].queryset = Company.objects.all().order_by('name')
        self.fields['department_parent'].queryset = Department.objects.filter(parent__isnull=True).order_by('order', 'name')
        self.fields['category_parent'].queryset = TicketCategory.objects.filter(parent__isnull=True).order_by('order', 'name')
        
        # Nếu có instance (edit mode), load department và category con
        if self.instance and self.instance.pk:
            if self.instance.department:
                if self.instance.department.parent:
                    # Department có parent, set parent và load các con
                    self.fields['department_parent'].initial = self.instance.department.parent.id
                    self.fields['department'].queryset = Department.objects.filter(
                        parent=self.instance.department.parent
                    ).order_by('order', 'name')
                    self.fields['department'].initial = self.instance.department.id
                else:
                    # Department là parent, chỉ set parent
                    self.fields['department_parent'].initial = self.instance.department.id
                    self.fields['department'].queryset = Department.objects.filter(
                        parent=self.instance.department
                    ).order_by('order', 'name')
            
            if self.instance.category:
                if self.instance.category.parent:
                    # Category có parent, set parent và load các con
                    self.fields['category_parent'].initial = self.instance.category.parent.id
                    self.fields['category'].queryset = TicketCategory.objects.filter(
                        parent=self.instance.category.parent
                    ).order_by('order', 'name')
                    self.fields['category'].initial = self.instance.category.id
                else:
                    # Category là parent, chỉ set parent
                    self.fields['category_parent'].initial = self.instance.category.id
                    self.fields['category'].queryset = TicketCategory.objects.filter(
                        parent=self.instance.category
                    ).order_by('order', 'name')

    def clean(self):
        cleaned_data = super().clean()
        
        # Lấy department từ department field (con) hoặc department_parent nếu không có con
        department = cleaned_data.get('department')
        department_parent = cleaned_data.get('department_parent')
        
        if not department and department_parent:
            # Nếu chọn parent nhưng không có con, dùng parent làm department
            department = department_parent
        
        # Validate department nếu có
        if department:
            # Nếu department có parent, phải có department_parent và phải khớp
            if department.parent:
                if not department_parent:
                    # Nếu chọn department con nhưng không chọn parent, tự động set parent
                    department_parent = department.parent
                    cleaned_data['department_parent'] = department_parent
                elif department.parent != department_parent:
                    raise forms.ValidationError({
                        'department': 'Phòng ban được chọn không hợp lệ với phòng ban cha.'
                    })
            # Nếu department không có parent nhưng có department_parent được chọn
            elif department_parent and department != department_parent:
                raise forms.ValidationError({
                    'department': 'Phòng ban được chọn không hợp lệ với phòng ban cha.'
                })
        
        # Lấy category từ category field (con) hoặc category_parent nếu không có con
        category = cleaned_data.get('category')
        category_parent = cleaned_data.get('category_parent')
        
        if not category and category_parent:
            # Nếu chọn parent nhưng không có con, dùng parent làm category
            category = category_parent
        
        # Validate category nếu có
        if category:
            # Nếu category có parent, phải có category_parent và phải khớp
            if category.parent:
                if not category_parent:
                    # Nếu chọn category con nhưng không chọn parent, tự động set parent
                    category_parent = category.parent
                    cleaned_data['category_parent'] = category_parent
                elif category.parent != category_parent:
                    raise forms.ValidationError({
                        'category': 'Loại yêu cầu được chọn không hợp lệ với loại yêu cầu cha.'
                    })
            # Nếu category không có parent nhưng có category_parent được chọn
            elif category_parent and category != category_parent:
                raise forms.ValidationError({
                    'category': 'Loại yêu cầu được chọn không hợp lệ với loại yêu cầu cha.'
                })
        
        cleaned_data['department'] = department
        cleaned_data['category'] = category
        return cleaned_data
    
    def save(self, commit=True):
        ticket = super().save(commit=False)
        
        # Set department và category từ cleaned_data
        ticket.department = self.cleaned_data.get('department')
        ticket.category = self.cleaned_data.get('category')
        
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

