from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Transaction
from .tasks import async_send_transaction_email

# Temporary store previous status
_old_status = {}

@receiver(pre_save, sender=Transaction)
def store_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            _old_status[instance.pk] = old.status
        except sender.DoesNotExist:
            _old_status[instance.pk] = None

@receiver(post_save, sender=Transaction)
def notify_user_on_transaction(sender, instance, created, **kwargs):
    old_status = _old_status.pop(instance.pk, None)
    if (
        instance.transaction_type in ['deposit', 'withdrawal']
        and instance.status == 'completed'
        and (created or old_status != 'completed')
    ):
        async_send_transaction_email.delay(str(instance.transaction_id))