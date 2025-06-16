from django.db import models
from django.utils import timezone
from bdounibank.models import BankAccount
import uuid
from django.conf import settings
class IMFCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)  # how many times used
    # (Consider storing code hashed for security)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"IMFCode({self.code})"

class COTCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"COTCode({self.code})"
    
    
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('loan_payment', 'Loan Payment'),
        ('interest', 'Interest'),
        ('fee', 'Fee'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    )
    
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(          #  ←  NEW
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='transactions',
    )
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    reference_number = models.CharField(max_length=50, blank=True)
    

    # Verification flags and attempt counters
    is_imf_verified = models.BooleanField(default=False)
    imf_attempts = models.PositiveIntegerField(default=0)
    is_cot_verified = models.BooleanField(default=False)
    cot_attempts = models.PositiveIntegerField(default=0)
    # Simulated additional steps
    step1_done = models.BooleanField(default=False)
    step2_done = models.BooleanField(default=False)
    step3_done = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.amount}"
    
    class Meta:
        ordering = ['-timestamp']

class VerificationLog(models.Model):
    CODE_TYPE_CHOICES = [
        ('IMF', 'IMF Code'),
        ('COT', 'COT Code'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    code_type = models.CharField(max_length=3, choices=CODE_TYPE_CHOICES)
    code_value = models.CharField(max_length=20)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} {self.code_type} for {self.user} at {self.timestamp}"

class Transfer(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, primary_key=True)
    source_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='outgoing_transfers')
    destination_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='incoming_transfers')
    
    def __str__(self):
        return f"Transfer from {self.source_account.account_number} to {self.destination_account.account_number}"