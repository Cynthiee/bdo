# loans/admin.py
from django.contrib import admin
from .models import LoanType, Loan, LoanPayment

@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'interest_rate', 'minimum_amount', 'maximum_amount', 'minimum_term', 'maximum_term')
    search_fields = ('name', 'description')
    list_filter = ('interest_rate',)

class LoanPaymentInline(admin.TabularInline):
    model = LoanPayment
    extra = 0
    readonly_fields = ('payment_id', 'payment_date')
    fields = ('payment_id', 'amount', 'payment_date', 'principal_component', 'interest_component')

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_id', 'borrower', 'loan_type', 'amount', 'interest_rate', 'status', 'application_date')
    list_filter = ('status', 'loan_type', 'application_date')
    search_fields = ('loan_id', 'borrower__username', 'borrower__first_name', 'borrower__last_name')
    readonly_fields = ('loan_id', 'application_date', 'monthly_payment')
    date_hierarchy = 'application_date'
    inlines = [LoanPaymentInline]
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('loan_id', 'borrower', 'loan_type', 'linked_account')
        }),
        ('Financial Details', {
            'fields': ('amount', 'interest_rate', 'term_months', 'monthly_payment')
        }),
        ('Status and Dates', {
            'fields': ('status', 'application_date', 'approval_date', 'disbursal_date', 'next_payment_date', 'final_payment_date')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new loan
            obj.monthly_payment = obj.calculate_monthly_payment()
        super().save_model(request, obj, form, change)

@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'loan', 'amount', 'payment_date', 'principal_component', 'interest_component')
    list_filter = ('payment_date',)
    search_fields = ('payment_id', 'loan__loan_id', 'loan__borrower__username')
    readonly_fields = ('payment_id',)
    date_hierarchy = 'payment_date'