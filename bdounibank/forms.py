from django import forms
from .models import BankAccount, AccountType

class BankAccountCreationForm(forms.ModelForm):
    account_type = forms.ModelChoiceField(
        queryset=AccountType.objects.all(),
        empty_label=None
    )
    initial_deposit = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        min_value=0.01
    )
    
    class Meta:
        model = BankAccount
        fields = ['account_type']
        
    def clean_initial_deposit(self):
        account_type = self.cleaned_data.get('account_type')
        initial_deposit = self.cleaned_data.get('initial_deposit')
        
        if account_type and initial_deposit:
            if initial_deposit < account_type.minimum_balance:
                raise forms.ValidationError(
                    f"Initial deposit must be at least {account_type.minimum_balance} for this account type."
                )
        
        return initial_deposit