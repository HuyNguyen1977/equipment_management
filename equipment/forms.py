from django import forms
from django.contrib.auth.models import User
from .models import Company, Equipment, EquipmentHistory
from .parser import parse_dxdiag
import os


class EquipmentForm(forms.ModelForm):
    """Form cho thiết bị"""
    dxdiag_file_upload = forms.FileField(
        required=False,
        label="Upload file DxDiag.txt (cho Laptop/Desktop)",
        help_text="Chọn file DxDiag.txt để tự động điền thông tin"
    )
    technical_specs_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'textarea', 'rows': 6}),
        label="Thông số kỹ thuật",
        help_text="Nhập thông số (mỗi dòng một cặp Tên: Giá trị)"
    )
    
    class Meta:
        model = Equipment
        fields = [
            'company', 'region', 'name', 'code', 'equipment_type', 'commission_date',
            'machine_name', 'operating_system', 'system_manufacturer', 
            'system_model', 'processor', 'memory', 'storage', 'graphics_card',
            'monitor_name', 'monitor_model',
            'documentation', 'current_user', 'is_active'
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'select'}),
            'region': forms.Select(attrs={'class': 'select', 'id': 'id_region'}),
            'name': forms.TextInput(attrs={'class': 'input'}),
            'code': forms.TextInput(attrs={'class': 'input', 'id': 'id_code', 'readonly': True}),
            'equipment_type': forms.Select(attrs={'class': 'select'}),
            'commission_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'machine_name': forms.TextInput(attrs={'class': 'input'}),
            'operating_system': forms.TextInput(attrs={'class': 'input'}),
            'system_manufacturer': forms.TextInput(attrs={'class': 'input'}),
            'system_model': forms.TextInput(attrs={'class': 'input'}),
            'processor': forms.TextInput(attrs={'class': 'input'}),
            'memory': forms.TextInput(attrs={'class': 'input'}),
            'storage': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ví dụ: SSD 256GB, HDD 1TB'}),
            'graphics_card': forms.TextInput(attrs={'class': 'input'}),
            'monitor_name': forms.TextInput(attrs={'class': 'input'}),
            'monitor_model': forms.TextInput(attrs={'class': 'input'}),
            'documentation': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'current_user': forms.Select(attrs={'class': 'select', 'id': 'id_current_user'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = Company.objects.all()
        self.fields['current_user'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['current_user'].required = False
        self.fields['current_user'].empty_label = "Chưa giao cho ai"
        
        # Nếu là tạo mới, tự động tạo code
        if not self.instance.pk:
            self.fields['code'].required = False
            self.fields['code'].help_text = "Mã sẽ được tự động tạo dựa trên miền"
        else:
            # Nếu đang sửa, cho phép chỉnh sửa code nhưng readonly
            # Nếu thay đổi miền, mã sẽ được tự động tạo lại
            self.fields['code'].help_text = "Mã thiết bị (chỉ đọc). Nếu thay đổi miền, mã sẽ được tự động tạo lại."
        
        # Khởi tạo technical_specs_text từ instance nếu có
        if self.instance and self.instance.pk and self.instance.technical_specs:
            specs_text = '\n'.join([f"{k}: {v}" for k, v in self.instance.technical_specs.items()])
            self.fields['technical_specs_text'].initial = specs_text
        
        # Ẩn các trường DxDiag nếu không phải laptop/desktop
        if self.instance and self.instance.pk:
            if self.instance.equipment_type not in ['laptop', 'desktop']:
                for field in ['machine_name', 'operating_system', 'system_manufacturer', 
                             'system_model', 'processor', 'memory', 'storage', 'graphics_card',
                             'monitor_name', 'monitor_model']:
                    self.fields[field].widget = forms.HiddenInput()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Tự động tạo code nếu chưa có (chỉ khi tạo mới)
        if not instance.code and instance.region:
            from .models import Equipment
            import re
            
            # Lấy prefix từ region
            prefix = instance.region
            
            # Tìm số lớn nhất trong miền này
            existing_codes = Equipment.objects.filter(
                code__startswith=f"{prefix}-"
            ).exclude(pk=instance.pk if instance.pk else None).values_list('code', flat=True)
            
            max_num = 0
            for code in existing_codes:
                match = re.match(rf'^{prefix}-(\d+)$', code)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            
            # Tạo code mới
            new_num = max_num + 1
            instance.code = f"{prefix}-{new_num:03d}"
        
        # Xử lý technical_specs từ text
        specs_text = self.cleaned_data.get('technical_specs_text', '')
        if specs_text:
            specs = {}
            for line in specs_text.split('\n'):
                line = line.strip()
                if line and ':' in line:
                    key, value = line.split(':', 1)
                    specs[key.strip()] = value.strip()
            instance.technical_specs = specs
        
        # Xử lý file DxDiag nếu có
        dxdiag_file = self.cleaned_data.get('dxdiag_file_upload')
        if dxdiag_file and instance.equipment_type in ['laptop', 'desktop']:
            # Lưu file
            instance.dxdiag_file = dxdiag_file
            
            # Parse file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                for chunk in dxdiag_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                parsed_data = parse_dxdiag(tmp_file_path)
                
                # Điền thông tin vào instance
                if parsed_data['machine_name']:
                    instance.machine_name = parsed_data['machine_name']
                if parsed_data['operating_system']:
                    instance.operating_system = parsed_data['operating_system']
                if parsed_data['system_manufacturer']:
                    instance.system_manufacturer = parsed_data['system_manufacturer']
                if parsed_data['system_model']:
                    instance.system_model = parsed_data['system_model']
                if parsed_data['processor']:
                    instance.processor = parsed_data['processor']
                if parsed_data['memory']:
                    instance.memory = parsed_data['memory']
                if parsed_data['graphics_card']:
                    instance.graphics_card = parsed_data['graphics_card']
                if parsed_data.get('monitor_name'):
                    instance.monitor_name = parsed_data['monitor_name']
                if parsed_data.get('monitor_model'):
                    instance.monitor_model = parsed_data['monitor_model']
                if parsed_data['technical_specs']:
                    # Merge với technical_specs hiện có
                    current_specs = instance.technical_specs or {}
                    current_specs.update(parsed_data['technical_specs'])
                    instance.technical_specs = current_specs
            finally:
                # Xóa file tạm
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
        
        if commit:
            instance.save()
        return instance


class EquipmentHistoryForm(forms.ModelForm):
    """Form cho lịch sử thiết bị"""
    to_user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=False,
        label="Chuyển đến người dùng",
        help_text="Chọn người dùng nhận thiết bị (chỉ áp dụng cho Di chuyển)",
        widget=forms.Select(attrs={'class': 'select', 'id': 'id_to_user'}),
        empty_label="Chọn người dùng..."
    )
    
    class Meta:
        model = EquipmentHistory
        fields = ['action_date', 'action_type', 'description', 'signed_by']
        widgets = {
            'action_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'action_type': forms.Select(attrs={'class': 'select', 'id': 'id_action_type'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 4}),
            'signed_by': forms.TextInput(attrs={'class': 'input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ẩn trường to_user mặc định, sẽ hiển thị bằng JavaScript khi chọn "Di chuyển"
        self.fields['to_user'].widget.attrs['style'] = 'display: none;'
        
        # Nếu đang edit và là movement, cố gắng parse to_user từ description
        if self.instance and self.instance.pk and self.instance.action_type == 'movement':
            description = self.instance.description
            if 'sang' in description:
                parts = description.split('sang')
                if len(parts) > 1:
                    username = parts[1].strip()
                    try:
                        user = User.objects.get(username=username)
                        self.fields['to_user'].initial = user.pk
                    except User.DoesNotExist:
                        pass

