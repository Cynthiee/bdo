# transactions/tasks.py
from celery import shared_task
from .models import Transaction
from .utils import send_transaction_email_with_receipt

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_send_transaction_email(self, transaction_id):
    from django.core.exceptions import ObjectDoesNotExist
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
    except ObjectDoesNotExist:
        return
    if transaction.transaction_type in ['deposit', 'withdrawal'] and transaction.status == 'completed':
        try:
            send_transaction_email_with_receipt(transaction)
        except Exception as e:
            # Retry on failure
            try:
                raise self.retry(exc=e)
            except AttributeError:
                # If retry not available, just log
                import logging; logging.getLogger(__name__).error(f"Email task error: {e}")
