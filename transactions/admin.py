# transactions/admin.py

from django.contrib import admin, messages
from .models import Transaction, Transfer,IMFCode, COTCode, VerificationLog

@admin.register(IMFCode)
class IMFCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'active', 'usage_count', 'created_at')
    list_filter = ('active',)
    search_fields = ('code',)

@admin.register(COTCode)
class COTCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'active', 'usage_count', 'created_at')
    list_filter = ('active',)
    search_fields = ('code',)

class TransferInline(admin.StackedInline):
    model = Transfer
    can_delete = False
    verbose_name_plural = 'Transfer Details'
    fk_name = 'transaction'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id',
        'account',
        'transaction_type',
        'amount',
        'status',
        'timestamp',
    )
    list_filter = ('transaction_type', 'is_imf_verified', 'is_cot_verified', 'completed', 'status', 'timestamp')
    search_fields = (
        'transaction_id',
        'account__account_number',
        'description',
        'reference_number',
    )
    readonly_fields = ('transaction_id', 'timestamp')
    date_hierarchy = 'timestamp'
    inlines = [TransferInline]

    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'account', 'transaction_type', 'amount', 'status'),
        }),
        ('Details', {
            'fields': ('description', 'reference_number', 'timestamp'),
        }),
    )

    actions = ['approve_transactions']

@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction', 'code_type', 'code_value', 'success', 'timestamp')
    list_filter = ('code_type', 'success', 'timestamp')
    search_fields = ('user__username', 'code_value')

    def approve_transactions(self, request, queryset):
        updated = 0
        for tx in queryset:
            if tx.status != 'completed':
                tx.status = 'completed'
                tx.save()
                updated += 1

        self.message_user(
            request,
            f"{updated} transaction(s) marked as completed.",
            messages.SUCCESS
        )

    approve_transactions.short_description = (
        "Approve selected transactions (status → completed)"
    )

    def save_model(self, request, obj, form, change):
        """
        Let the signals handle email sending when status flips to 'completed'.
        """
        super().save_model(request, obj, form, change)


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'source_account', 'destination_account')
    search_fields = (
        'transaction__transaction_id',
        'source_account__account_number',
        'destination_account__account_number',
    )

    def has_add_permission(self, request):
        return False
