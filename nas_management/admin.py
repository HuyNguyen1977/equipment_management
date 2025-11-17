from django.contrib import admin
from .models import NASConfig, LoginHistory, SystemStats, NASLog, FileOperation


@admin.register(NASConfig)
class NASConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'port', 'use_https', 'is_active', 'created_at']
    list_filter = ['is_active', 'use_https']
    search_fields = ['name', 'host']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'is_active')
        }),
        ('Cấu hình kết nối', {
            'fields': ('host', 'port', 'use_https'),
            'description': 'Host: chỉ nhập IP hoặc domain (ví dụ: 192.168.1.100 hoặc nas.example.com), KHÔNG bao gồm http:// hoặc https://'
        }),
        ('Thông tin đăng nhập', {
            'fields': ('username', 'password')
        }),
        ('Thông tin khác', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['nas', 'username', 'ip_address', 'login_time', 'is_success', 'failure_reason']
    list_filter = ['nas', 'is_success', 'login_time']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['created_at']
    date_hierarchy = 'login_time'


@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    list_display = ['nas', 'cpu_usage', 'memory_usage', 'timestamp']
    list_filter = ['nas', 'timestamp']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(NASLog)
class NASLogAdmin(admin.ModelAdmin):
    list_display = ['nas', 'level', 'category', 'message', 'timestamp']
    list_filter = ['nas', 'level', 'category', 'timestamp']
    search_fields = ['message', 'category', 'source']
    readonly_fields = ['created_at']
    date_hierarchy = 'timestamp'


@admin.register(FileOperation)
class FileOperationAdmin(admin.ModelAdmin):
    list_display = ['nas', 'user', 'operation', 'file_path', 'is_success', 'timestamp']
    list_filter = ['nas', 'operation', 'is_success', 'timestamp']
    search_fields = ['file_path', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
