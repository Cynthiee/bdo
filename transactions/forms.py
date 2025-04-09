from django import forms
from bdounibank.models import BankAccount
from .models import Transaction

class DepositForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=None,
        empty_label=None
    )
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        min_value=0.01
    )
    description = forms.CharField(
        max_length=255, 
        required=False
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = BankAccount.objects.filter(
            owner=user,
            status='active'
        )

class WithdrawalForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=None,
        empty_label=None
    )
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        min_value=0.01
    )
    description = forms.CharField(
        max_length=255, 
        required=False
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = BankAccount.objects.filter(
            owner=user,
            status='active'
        )
    
    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        amount = cleaned_data.get('amount')
        
        if account and amount:
            if amount > account.balance:
                raise forms.ValidationError("Insufficient funds for this withdrawal.")
            
            if account.balance - amount < account.account_type.minimum_balance:
                raise forms.ValidationError(
                    f"This withdrawal would put your account below the minimum balance of {account.account_type.minimum_balance}."
                )
        
        return cleaned_data

class TransferForm(forms.Form):
    source_account = forms.ModelChoiceField(
        queryset=None,
        empty_label=None,
        label="From Account"
    )
    destination_account_number = forms.CharField(
        max_length=20,
        label="To Account Number"
    )
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        min_value=0.01
    )
    description = forms.CharField(
        max_length=255, 
        required=False
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source_account'].queryset = BankAccount.objects.filter(
            owner=user,
            status='active'
        )
    
    def clean(self):
        cleaned_data = super().clean()
        source_account = cleaned_data.get('source_account')
        destination_account_number = cleaned_data.get('destination_account_number')
        amount = cleaned_data.get('amount')
        
        if source_account and destination_account_number and amount:
            # Check if destination account exists
            try:
                destination_account = BankAccount.objects.get(
                    account_number=destination_account_number,
                    status='active'
                )
                cleaned_data['destination_account'] = destination_account
            except BankAccount.DoesNotExist:
                raise forms.ValidationError("Destination account not found or inactive.")
            
            # Check if trying to transfer to self
            if source_account == destination_account:
                raise forms.ValidationError("Cannot transfer to the same account.")
            
            # Check sufficient funds
            if amount > source_account.balance:
                raise forms.ValidationError("Insufficient funds for this transfer.")
            
            # Check minimum balance requirement
            if source_account.balance - amount < source_account.account_type.minimum_balance:
                raise forms.ValidationError(
                    f"This transfer would put your account below the minimum balance of {source_account.account_type.minimum_balance}."
                )
        
        return cleaned_data