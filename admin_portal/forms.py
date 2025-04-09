from django import forms
from accounts.models import User
from bdounibank.models import BankAccount
from loans.models import Loan

class UserSearchForm(forms.Form):
    search_term = forms.CharField(max_length=100, required=False)
    user_type = forms.ChoiceField(
        choices=[('', 'All')] + list(User.USER_TYPE_CHOICES),
        required=False
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('active', 'Active'),
            ('inactive', 'Inactive')
        ],
        required=False
    )

class AccountSearchForm(forms.Form):
    search_term = forms.CharField(max_length=100, required=False)
    account_status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('suspended', 'Suspended'),
            ('closed', 'Closed')
        ],
        required=False
    )

class LoanApprovalForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject')
        ]
    )
    notes = forms.CharField(widget=forms.Textarea, required=False)
    
    def __init__(self, loan_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loan_id = loan_id

