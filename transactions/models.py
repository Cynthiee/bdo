from django.db import models
from django.utils import timezone
from bdounibank.models import BankAccount
import uuid

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
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    reference_number = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.amount}"
    
    class Meta:
        ordering = ['-timestamp']

class Transfer(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, primary_key=True)
    source_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='outgoing_transfers')
    destination_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='incoming_transfers')
    
    def __str__(self):
        return f"Transfer from {self.source_account.account_number} to {self.destination_account.account_number}"