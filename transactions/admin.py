# transactions/admin.py
from django.contrib import admin
from .models import Transaction, Transfer

class TransferInline(admin.StackedInline):
    model = Transfer
    can_delete = False
    verbose_name_plural = 'Transfer Details'
    fk_name = 'transaction'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'account', 'transaction_type', 'amount', 'status', 'timestamp')
    list_filter = ('transaction_type', 'status', 'timestamp')
    search_fields = ('transaction_id', 'account__account_number', 'description', 'reference_number')
    readonly_fields = ('transaction_id', 'timestamp')
    date_hierarchy = 'timestamp'
    inlines = [TransferInline]
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'account', 'transaction_type', 'amount', 'status')
        }),
        ('Details', {
            'fields': ('description', 'reference_number', 'timestamp')
        }),
    )

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'source_account', 'destination_account')
    search_fields = ('transaction__transaction_id', 'source_account__account_number', 'destination_account__account_number')
    
    def has_add_permission(self, request):
        # Transfers should only be created along with Transactions
        return False