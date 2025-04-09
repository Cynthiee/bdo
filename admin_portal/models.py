from django.db import models
from accounts.models import User
from django.utils import timezone

class AuditLog(models.Model):
    ACTION_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=10, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    resource_type = models.CharField(max_length=100)  # e.g., 'BankAccount', 'Loan', etc.
    resource_id = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.action} by {self.user} on {self.resource_type} ({self.timestamp})"
    
    class Meta:
        ordering = ['-timestamp']

class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField()
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.key