from django.db import models
from django.utils import timezone
from accounts.models import User
from bdounibank.models import BankAccount
import uuid

class LoanType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Annual percentage
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    maximum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_term = models.IntegerField()  # In months
    maximum_term = models.IntegerField()  # In months
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class Loan(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('paid', 'Paid'),
        ('defaulted', 'Defaulted'),
        ('closed', 'Closed'),
    )
    
    loan_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Annual percentage
    term_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    linked_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, related_name='linked_loans')
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    disbursal_date = models.DateTimeField(null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    final_payment_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Loan {self.loan_id} - {self.borrower.username} - {self.status}"
    
    def calculate_monthly_payment(self):
        # Convert annual rate to monthly rate
        monthly_rate = self.interest_rate / 12 / 100
        
        # Formula for EMI: P * r * (1+r)^n / ((1+r)^n - 1)
        numerator = self.amount * monthly_rate * (1 + monthly_rate) ** self.term_months
        denominator = (1 + monthly_rate) ** self.term_months - 1
        
        if denominator == 0:  # For interest-free loans
            return self.amount / self.term_months
            
        return numerator / denominator

class LoanPayment(models.Model):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    principal_component = models.DecimalField(max_digits=12, decimal_places=2)
    interest_component = models.DecimalField(max_digits=12, decimal_places=2)
    transaction = models.OneToOneField('transactions.Transaction', on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"Payment {self.payment_id} for Loan {self.loan.loan_id}"
    
    class Meta:
        ordering = ['-payment_date']