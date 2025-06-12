from django.contrib import admin, messages
from .models import Transaction, Transfer
from transactions.utils import send_transaction_email_with_receipt


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

    actions = ['approve_transactions']

    def approve_transactions(self, request, queryset):
        updated = 0
        emailed = 0
        for transaction in queryset:
            original_status = transaction.status
            if original_status != 'completed':
                transaction.status = 'completed'
                transaction.save()
                updated += 1

            send_transaction_email_with_receipt(transaction)
            emailed += 1

        self.message_user(
            request,
            f"{updated} transaction(s) marked as completed. {emailed} email(s) sent.",
            messages.SUCCESS
        )

    approve_transactions.short_description = "Approve selected transactions and send email"

    def save_model(self, request, obj, form, change):
        # Check if status changed to completed before saving
        send_email = False
        if change:
            original = Transaction.objects.get(pk=obj.pk)
            if original.status != 'completed' and obj.status == 'completed':
                send_email = True

        super().save_model(request, obj, form, change)

        if send_email:
            send_transaction_email_with_receipt(obj)


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'source_account', 'destination_account')
    search_fields = (
        'transaction__transaction_id',
        'source_account__account_number',
        'destination_account__account_number',
    )

    def has_add_permission(self, request):
        # Transfers should only be created along with Transactions
        return False
