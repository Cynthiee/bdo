# transactions/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction
from .tasks import async_send_transaction_email

@receiver(post_save, sender=Transaction)
def notify_user_on_transaction(sender, instance, created, **kwargs):
    # Trigger when a transaction is created or updated to completed.
    # If using created-only and you set status='completed' on creation, use created.
    # If status changes later, you may check previous state in update flows.
    if instance.transaction_type in ['deposit', 'withdrawal'] and instance.status == 'completed':
        # Enqueue Celery task
        async_send_transaction_email.delay(str(instance.transaction_id))
