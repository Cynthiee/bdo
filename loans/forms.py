from django import forms
from django.utils import timezone
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
    term_months = forms.IntegerField(
        min_value=1,
        help_text="Loan duration in months"
    )
    
    class Meta:
        model = Loan
        fields = ['loan_type', 'amount', 'term_months', 'linked_account']
        
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['linked_account'].queryset = BankAccount.objects.filter(
            owner=user,
            status='active'
        )
        self.user = user
    
    def clean(self):
        cleaned_data = super().clean()
        loan_type = cleaned_data.get('loan_type')
        amount = cleaned_data.get('amount')
        term_months = cleaned_data.get('term_months')
        
        if loan_type and amount and term_months:
            # Validate amount is within loan type limits
            if amount < loan_type.minimum_amount:
                raise forms.ValidationError(f"Loan amount must be at least {loan_type.minimum_amount}.")
            if amount > loan_type.maximum_amount:
                raise forms.ValidationError(f"Loan amount cannot exceed {loan_type.maximum_amount}.")
            
            # Validate term is within loan type limits
            if term_months < loan_type.minimum_term:
                raise forms.ValidationError(f"Loan term must be at least {loan_type.minimum_term} months.")
            if term_months > loan_type.maximum_term:
                raise forms.ValidationError(f"Loan term cannot exceed {loan_type.maximum_term} months.")
        
        return cleaned_data
    
    def save(self, commit=True):
        loan = super().save(commit=False)
        loan.borrower = self.user
        loan.interest_rate = self.cleaned_data['loan_type'].interest_rate
        
        # Calculate and set monthly payment
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
        self.fields['loan'].queryset = Loan.objects.filter(
            borrower=user,
            status='active'
        )
        self.fields['payment_account'].queryset = BankAccount.objects.filter(
            owner=user,
            status='active'
        )
    
    def clean(self):
        cleaned_data = super().clean()
        payment_account = cleaned_data.get('payment_account')
        payment_amount = cleaned_data.get('payment_amount')
        
        if payment_account and payment_amount:
            # Check sufficient funds
            if payment_amount > payment_account.balance:
                raise forms.ValidationError("Insufficient funds for this payment.")
            
            # Check minimum balance requirement
            if payment_account.balance - payment_amount < payment_account.account_type.minimum_balance:
                raise forms.ValidationError(
                    f"This payment would put your account below the minimum balance of {payment_account.account_type.minimum_balance}."
                )
        
        return cleaned_data