import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Transaction
from .utils import send_transaction_email_with_receipt

logger = logging.getLogger(__name__)

# In-memory store of old statuses to detect changes
_old_status = {}

@receiver(pre_save, sender=Transaction)
def store_old_status(sender, instance, **kwargs):
    """
    Before saving, capture the old status for comparison.
    """
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            _old_status[instance.pk] = old.status
        except sender.DoesNotExist:
            _old_status[instance.pk] = None

@receiver(post_save, sender=Transaction)
def auto_send_email_on_complete(sender, instance, created, **kwargs):
    """
    After save, if this is a deposit/withdrawal and the status
    just became 'completed', send the email + receipt.
    """
    old_status = _old_status.pop(instance.pk, None)

    # Only for deposits and withdrawals
    if instance.transaction_type in ('deposit', 'withdrawal'):
        # Case A: newly created and already completed:
        if created and instance.status == 'completed':
            send_transaction_email_with_receipt(instance)
            logger.info(f"Auto-email sent for new completed transaction {instance.transaction_id}")

        # Case B: existing record whose status just changed to 'completed':
        elif not created and old_status != 'completed' and instance.status == 'completed':
            send_transaction_email_with_receipt(instance)
            logger.info(f"Auto-email sent for updated transaction {instance.transaction_id}")