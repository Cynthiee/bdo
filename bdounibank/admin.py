# bdounibank/admin.py
from django.contrib import admin
from .models import AccountType, BankAccount
from django.utils.html import format_html

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'minimum_balance', 'interest_rate', 'maintenance_fee')
    search_fields = ('name', 'description')
    list_filter = ('interest_rate',)

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'get_owner_name', 'account_type', 'balance', 'status', 'created_at', 'last_activity')
    list_filter = ('status', 'account_type', 'created_at')
    search_fields = ('account_number', 'owner__username', 'owner__first_name', 'owner__last_name')
    readonly_fields = ('created_at', 'last_activity')
    date_hierarchy = 'created_at'
    
    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}" if obj.owner.first_name else obj.owner.username
    get_owner_name.short_description = 'Owner'
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_number', 'account_type', 'owner', 'balance', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    def balance_display(self, obj):
        if obj.balance < 0:
            return format_html('<span style="color:red;">${}</span>', obj.balance)
        return f"${obj.balance}"
    balance_display.short_description = 'Balance'