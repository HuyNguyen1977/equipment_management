from django.contrib import admin
from .models import RenewalType, Renewal, RenewalHistory


@admin.register(RenewalType)
class RenewalTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'description']
    list_editable = ['order']
    search_fields = ['name', 'description']


@admin.register(Renewal)
class RenewalAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'renewal_type', 'company', 'expiry_date',
        'days_until_expiry', 'status', 'responsible_person'
    ]
    list_filter = ['renewal_type', 'status', 'company', 'expiry_date']
    search_fields = ['name', 'description', 'provider']
    date_hierarchy = 'expiry_date'
    readonly_fields = ['created_at', 'updated_at', 'days_until_expiry']
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('renewal_type', 'name', 'description', 'company')
        }),
        ('Thông tin gia hạn', {
            'fields': (
                'start_date', 'expiry_date', 'renewal_period',
                'cost', 'auto_renewal', 'status'
            )
        }),
        ('Nhà cung cấp', {
            'fields': ('provider', 'provider_contact')
        }),
        ('Quản lý', {
            'fields': ('responsible_person', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RenewalHistory)
class RenewalHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'renewal', 'renewal_date', 'old_expiry_date',
        'new_expiry_date', 'cost', 'renewed_by'
    ]
    list_filter = ['renewal_date', 'renewal__renewal_type']
    search_fields = ['renewal__name', 'notes']
    date_hierarchy = 'renewal_date'
    readonly_fields = ['created_at']
