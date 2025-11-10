from django.contrib import admin
from .models import Company, Department, TicketCategory, Ticket, TicketComment, TicketAttachment


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'company', 'created_at']
    list_filter = ['company', 'parent', 'created_at']
    search_fields = ['name']
    raw_id_fields = ['parent', 'company']


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name']
    raw_id_fields = ['parent']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_number', 'title', 'requester_name', 'company', 
        'status', 'priority', 'assigned_to', 'created_at'
    ]
    list_filter = ['status', 'priority', 'company', 'category', 'created_at']
    search_fields = ['ticket_number', 'title', 'requester_name', 'requester_email']
    raw_id_fields = ['requester', 'company', 'department', 'category', 'assigned_to']
    readonly_fields = ['ticket_number', 'created_at', 'updated_at', 'resolved_at', 'repeat_count']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('ticket_number', 'title', 'description', 'status', 'priority')
        }),
        ('Thông tin người yêu cầu', {
            'fields': ('requester', 'requester_name', 'requester_email', 'requester_phone')
        }),
        ('Thông tin công ty và phòng ban', {
            'fields': ('company', 'department')
        }),
        ('Phân loại', {
            'fields': ('category',)
        }),
        ('Xử lý', {
            'fields': ('assigned_to', 'resolution', 'resolved_at', 'repeat_count')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['content', 'ticket__ticket_number']
    raw_id_fields = ['ticket', 'author']


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'filename', 'uploaded_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['filename', 'ticket__ticket_number']
    raw_id_fields = ['ticket', 'uploaded_by']
