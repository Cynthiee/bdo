# admin_portal/context_processors.py
from transactions.models import Transaction

def pending_transaction_count(request):
    """
    Provide count of pending deposit/withdrawal transactions for admin/staff.
    """
    user = request.user
    if user.is_authenticated and getattr(user, 'user_type', None) in ['admin','staff']:
        count = Transaction.objects.filter(
            status='pending',
            transaction_type__in=['deposit','withdrawal']
        ).count()
        return {'pending_transaction_count': count}
    return {}
