from decimal import Decimal
from django import forms
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Loan, LoanType
from bdounibank.models import BankAccount

class LoanApplicationForm(forms.ModelForm):
    loan_type = forms.ModelChoiceField(
        queryset=LoanType.objects.all(),
        empty_label=None
    )
    linked_account = forms.ModelChoiceField(
        queryset=None,
        empty_label=None,
        help_text="Account where loan funds will be deposited and payments withdrawn"
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01
    )
    term_months = forms.IntegerField(
        min_value=1,
        help_text="Loan duration in months"
    )
    purpose = forms.CharField(
        max_length=255,
        required=True,
        help_text="Briefly state the purpose of this loan"
    )

    class Meta:
        model = Loan
        fields = ['loan_type', 'amount', 'term_months', 'linked_account', 'purpose']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['linked_account'].queryset = BankAccount.objects.filter(
            owner=user,
            status='active'
        )

        # Crispy helper setup
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Apply for Loan'))

    def clean(self):
        cleaned_data = super().clean()
        loan_type = cleaned_data.get('loan_type')
        amount = cleaned_data.get('amount')
        term_months = cleaned_data.get('term_months')
        linked_account = cleaned_data.get('linked_account')

        if linked_account and linked_account.owner != self.user:
            self.add_error('linked_account', "You do not own the selected account.")

        if loan_type and amount:
            if amount < loan_type.minimum_amount:
                self.add_error('amount', f"Loan amount must be at least {loan_type.minimum_amount}.")
            if amount > loan_type.maximum_amount:
                self.add_error('amount', f"Loan amount cannot exceed {loan_type.maximum_amount}.")

        if loan_type and term_months:
            if term_months < loan_type.minimum_term:
                self.add_error('term_months', f"Loan term must be at least {loan_type.minimum_term} months.")
            if term_months > loan_type.maximum_term:
                self.add_error('term_months', f"Loan term cannot exceed {loan_type.maximum_term} months.")

        return cleaned_data

    def save(self, commit=True):
        loan = super().save(commit=False)
        loan.borrower = self.user
        loan.interest_rate = self.cleaned_data['loan_type'].interest_rate
        loan.monthly_payment = loan.calculate_monthly_payment()

        if commit:
            loan.save()
        return loan


class LoanPaymentForm(forms.Form):
    loan = forms.ModelChoiceField(
        queryset=None,
        empty_label=None
    )
    payment_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01
    )
    payment_account = forms.ModelChoiceField(
        queryset=None,
        empty_label=None,
        help_text="Account to withdraw payment from"
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['loan'].queryset = Loan.objects.filter(
            borrower=user,
            status='active'
        )
        self.fields['payment_account'].queryset = BankAccount.objects.filter(
            owner=user,
            status='active'
        )

        # Crispy helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Pay Loan'))

    def clean(self):
        cleaned_data = super().clean()
        payment_account = cleaned_data.get('payment_account')
        payment_amount = cleaned_data.get('payment_amount')

        if payment_account and payment_account.owner != self.user:
            self.add_error('payment_account', "You do not own this account.")

        if payment_account and payment_amount:
            if payment_amount > payment_account.balance:
                self.add_error('payment_amount', "Insufficient funds for this payment.")

            min_balance = payment_account.account_type.minimum_balance
            if payment_account.balance - payment_amount < min_balance:
                self.add_error(
                    'payment_amount',
                    f"This payment would reduce your balance below the minimum required: {min_balance}."
                )

        return cleaned_data
