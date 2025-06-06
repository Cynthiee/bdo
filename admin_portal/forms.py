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

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        # Allow the admin to change these fields:
        fields = [
            'account_type',
            'owner',
            'status',
            'balance',
        ]

        widgets = {
            # Tailwind‐style classes on each widget
            'account_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm '
                         'focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'owner': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm '
                         'focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm '
                         'focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm '
                         'focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        We override __init__ so that the "owner" dropdown only shows Users of type 'customer'.
        If you want staff/admin to be selectable too, drop the filter.
        """
        super().__init__(*args, **kwargs)
        # Only allow choosing from customers (not staff/admin)
        self.fields['owner'].queryset = User.objects.filter(user_type='customer')
