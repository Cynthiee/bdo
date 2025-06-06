from django.db import models
from django.utils import timezone
from accounts.models import User
from decimal import Decimal  # ← Import Decimal
import uuid

class AccountType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    minimum_balance = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Annual percentage
    maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class BankAccount(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    )
    
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.account_number} - {self.owner.username}"
    
    def deposit(self, amount):
        """
        Deposit a positive amount into the account. Converts `amount` to Decimal first.
        Raises ValueError if the (converted) amount is <= 0.
        """
        # Convert the incoming amount to Decimal
        amount_dec = Decimal(str(amount))
        
        if amount_dec <= Decimal('0'):
            raise ValueError("Deposit amount must be positive")
        
        # Now both self.balance and amount_dec are Decimals
        self.balance += amount_dec
        self.save()
        
    def withdraw(self, amount):
        """
        Withdraw a positive amount from the account. Converts `amount` to Decimal first.
        Raises ValueError if the (converted) amount is <= 0 or if it exceeds the balance.
        """
        amount_dec = Decimal(str(amount))
        
        if amount_dec <= Decimal('0'):
            raise ValueError("Withdrawal amount must be positive")
        if amount_dec > self.balance:
            raise ValueError("Insufficient funds")
        
        self.balance -= amount_dec
        self.save()
    
    def is_minimum_balance_maintained(self):
        return self.balance >= self.account_type.minimum_balance
