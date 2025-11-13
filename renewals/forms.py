from django import forms
from django.contrib.auth.models import User
from .models import Renewal, RenewalType, RenewalHistory
from equipment.models import Company


class RenewalForm(forms.ModelForm):
    """Form cho Renewal"""
    
    class Meta:
        model = Renewal
        fields = [
            'renewal_type', 'name', 'description',
            'start_date', 'expiry_date', 'renewal_period',
            'cost', 'provider', 'provider_contact',
            'company', 'responsible_person',
            'status', 'auto_renewal', 'notes'
        ]
        widgets = {
            'renewal_type': forms.Select(attrs={'class': 'select'}),
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ví dụ: Gmail Business, AWS Server, domain.com'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'renewal_period': forms.NumberInput(attrs={'class': 'input', 'min': 1, 'max': 60}),
            'cost': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'placeholder': 'VND'}),
            'provider': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Tên nhà cung cấp'}),
            'provider_contact': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Email, số điện thoại...'}),
            'company': forms.Select(attrs={'class': 'select'}),
            'responsible_person': forms.Select(attrs={'class': 'select is-fullwidth', 'id': 'id_responsible_person'}),
            'status': forms.Select(attrs={'class': 'select'}),
            'auto_renewal': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'notes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['renewal_type'].queryset = RenewalType.objects.all().order_by('order', 'name')
        self.fields['company'].queryset = Company.objects.all().order_by('name')
        self.fields['responsible_person'].queryset = User.objects.filter(is_active=True).order_by('username')
        
        # Đặt required=False cho một số trường
        self.fields['description'].required = False
        self.fields['cost'].required = False
        self.fields['provider'].required = False
        self.fields['provider_contact'].required = False
        self.fields['company'].required = False
        self.fields['responsible_person'].required = False
        self.fields['notes'].required = False


class RenewalHistoryForm(forms.ModelForm):
    """Form cho RenewalHistory"""
    
    class Meta:
        model = RenewalHistory
        fields = ['renewal_date', 'old_expiry_date', 'new_expiry_date', 'cost', 'notes']
        widgets = {
            'renewal_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'old_expiry_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'new_expiry_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'cost': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'placeholder': 'VND'}),
            'notes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        renewal = kwargs.pop('renewal', None)
        super().__init__(*args, **kwargs)
        
        if renewal and not self.instance.pk:
            # Pre-fill với thông tin từ renewal hiện tại
            self.fields['old_expiry_date'].initial = renewal.expiry_date
            # Tính ngày hết hạn mới
            from datetime import timedelta
            new_expiry = renewal.expiry_date + timedelta(days=30 * renewal.renewal_period)
            self.fields['new_expiry_date'].initial = new_expiry
        
        self.fields['cost'].required = False
        self.fields['notes'].required = False

