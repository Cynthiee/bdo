# transactions/forms.py
from __future__ import annotations

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div
from bdounibank.models import BankAccount
from .models import Transaction


# ──────────────────────────────────────────────────────────────
#  Helper – one place to control look‑and‑feel
# ──────────────────────────────────────────────────────────────
class BaseHelper(FormHelper):
    """Reusable crispy‑forms helper with BDO/Mainwesthern styling."""
    primary_btn   = "bg-blue-700 hover:bg-blue-800 text-white"
    input_styles  = "mt-1 block w-full rounded-md border-gray-300 shadow-sm " \
                    "focus:ring-blue-600 focus:border-blue-600"
    label_styles  = "block text-sm font-medium text-gray-700"

    def __init__(self, show_submit: bool = True, submit_text: str = "Continue"):
        super().__init__()
        self.form_method = "post"
        self.label_class = self.label_styles
        self.field_class = ""
        # Build an **empty** layout first – then children can safely append
        self.layout = Layout()

        if show_submit:
            self.layout.append(
                Div(
                    Submit(
                        "submit",
                        submit_text,
                        css_class=f"w-full py-2 px-4 rounded {self.primary_btn}",
                    ),
                    css_class="pt-4",
                )
            )


# Convenience shortcut
def _account_queryset(user):
    return BankAccount.objects.filter(owner=user, status="active")


# ──────────────────────────────────────────────────────────────
#  1) IMF / COT – model forms
# ──────────────────────────────────────────────────────────────
class TransferRequestForm(forms.ModelForm):
    class Meta:
        model  = Transaction
        fields = ["account", "amount", "description"]
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "placeholder": "Amount ($)"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Optional description"}),
        }

    def __init__(self, *args, **kwargs):
        user   = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["account"].queryset = _account_queryset(user)
        self.fields["description"].required = False

        # Per‑form helper instance
        self.helper = BaseHelper()

    # --- validation identical to before ---
    def clean(self):
        cleaned = super().clean()
        account, amount = cleaned.get("account"), cleaned.get("amount")

        if account and amount:
            if amount > account.balance:
                raise forms.ValidationError("Insufficient funds for this transfer.")
            if account.balance - amount < account.account_type.minimum_balance:
                raise forms.ValidationError(
                    f"This transfer would drop the balance below the minimum "
                    f"required ({account.account_type.minimum_balance})."
                )
        return cleaned


class WithdrawalRequestForm(forms.ModelForm):
    class Meta:
        model  = Transaction
        fields = ["account", "amount", "description"]
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "placeholder": "Amount ($)"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Optional description"}),
        }

    def __init__(self, *args, **kwargs):
        user   = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["account"].queryset = _account_queryset(user)
        self.fields["description"].required = False
        self.helper = BaseHelper()

    def clean(self):
        cleaned = super().clean()
        account, amount = cleaned.get("account"), cleaned.get("amount")

        if account and amount:
            if amount > account.balance:
                raise forms.ValidationError("Insufficient funds for this withdrawal.")
            if account.balance - amount < account.account_type.minimum_balance:
                raise forms.ValidationError(
                    f"This withdrawal would drop the balance below the required "
                    f"minimum ({account.account_type.minimum_balance})."
                )
        return cleaned


# ──────────────────────────────────────────────────────────────
#  2) One‑field verification code form
# ──────────────────────────────────────────────────────────────
class CodeVerificationForm(forms.Form):
    code = forms.CharField(
        max_length=20,
        label="Verification Code",
        widget=forms.TextInput(attrs={"placeholder": "Enter code"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override helper: no auto‑submit; we provide our own button text
        self.helper = BaseHelper(show_submit=False)
        self.helper.layout = Layout(
            Field("code", css_class="mb-4"),
            Submit(
                "submit",
                "Verify Code",
                css_class=f"w-full py-2 px-4 rounded {BaseHelper.primary_btn}",
            ),
        )


# ──────────────────────────────────────────────────────────────
#  3) Legacy “instant” forms
# ──────────────────────────────────────────────────────────────
class DepositForm(forms.Form):
    account = forms.ModelChoiceField(queryset=BankAccount.objects.none())
    amount  = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01,
                                 widget=forms.NumberInput(attrs={"step": "0.01"}))
    description = forms.CharField(
        max_length=255, required=False, widget=forms.Textarea(attrs={"rows": 2})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = _account_queryset(user)
        self.helper = BaseHelper()

class WithdrawalForm(DepositForm):
    """Shares layout with Deposit; custom validation only."""
    def clean(self):
        cleaned = super().clean()
        acc, amt = cleaned.get("account"), cleaned.get("amount")
        if acc and amt:
            if amt > acc.balance:
                raise forms.ValidationError("Insufficient funds for this withdrawal.")
            if acc.balance - amt < acc.account_type.minimum_balance:
                raise forms.ValidationError(
                    f"This withdrawal would put your balance below "
                    f"the minimum ({acc.account_type.minimum_balance})."
                )
        return cleaned

class TransferForm(forms.Form):
    source_account = forms.ModelChoiceField(queryset=BankAccount.objects.none(), label="From")
    destination_account_number = forms.CharField(
        max_length=20, label="To account #", widget=forms.TextInput(attrs={"placeholder": "BDO‑XXXX"})
    )
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01,
                                widget=forms.NumberInput(attrs={"step": "0.01"}))
    description = forms.CharField(
        max_length=255, required=False, widget=forms.Textarea(attrs={"rows": 2})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_account"].queryset = _account_queryset(user)
        self.helper = BaseHelper()

    def clean(self):
        cleaned = super().clean()
        src   = cleaned.get("source_account")
        dst_no = cleaned.get("destination_account_number")
        amt   = cleaned.get("amount")

        if src and dst_no and amt:
            try:
                dst = BankAccount.objects.get(account_number=dst_no, status="active")
                cleaned["destination_account"] = dst
            except BankAccount.DoesNotExist:
                raise forms.ValidationError("Destination account not found or inactive.")

            if src == dst:
                raise forms.ValidationError("Cannot transfer to the same account.")
            if amt > src.balance:
                raise forms.ValidationError("Insufficient funds for this transfer.")
            if src.balance - amt < src.account_type.minimum_balance:
                raise forms.ValidationError(
                    f"This transfer would drop the balance below the minimum "
                    f"({src.account_type.minimum_balance})."
                )
        return cleaned
