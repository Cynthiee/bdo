# admin_portal/admin.py
from django.contrib import admin
from .models import AuditLog, SystemSetting

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'resource_type', 'resource_id', 'ip_address', 'timestamp')
    list_filter = ('action', 'resource_type', 'timestamp')
    search_fields = ('user__username', 'resource_type', 'resource_id', 'details', 'ip_address')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'last_modified', 'modified_by')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('last_modified',)
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description', 'modified_by')
        }),
        ('History', {
            'fields': ('last_modified',),
            'classes': ('collapse',)
        }),
    )