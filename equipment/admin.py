from django.contrib import admin
from .models import Company, Equipment, EquipmentHistory


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'equipment_type', 'current_user', 'commission_date', 'is_active']
    list_filter = ['company', 'equipment_type', 'is_active', 'current_user']
    search_fields = ['name', 'code', 'machine_name', 'current_user__username', 'current_user__first_name', 'current_user__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EquipmentHistory)
class EquipmentHistoryAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'action_date', 'action_type', 'signed_by']
    list_filter = ['action_type', 'action_date']
    search_fields = ['equipment__name', 'description', 'signed_by']
    readonly_fields = ['created_at']

