from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import BankAccount, AccountType
from .forms import BankAccountCreationForm
from transactions.models import Transaction
import uuid
from django.db.models import Sum
from decimal import Decimal

def landing_page_view(request):
    return render(request, 'landing_page.html')

# @login_required
# def dashboard_view(request):
#     accounts = BankAccount.objects.filter(owner=request.user)
#     total_balance = sum(account.balance for account in accounts)
    
#     # Get recent transactions
#     recent_transactions = Transaction.objects.filter(
#         account__in=accounts
#     ).order_by('-timestamp')[:5]
    
#     context = {
#         'accounts': accounts,
#         'total_balance': total_balance,
#         'recent_transactions': recent_transactions
#     }
#     return render(request, 'banking/dashboard.html', context)


@login_required
def dashboard_view(request):
    # 1. Fetch all accounts for this user
    accounts = BankAccount.objects.filter(owner=request.user)

    # 2. Use Django’s aggregate() so that the database returns a Decimal (or None)
    agg = accounts.aggregate(total=Sum('balance'))
    total_balance = agg['total'] if agg['total'] is not None else Decimal('0.00')

    # 3. Grab the 5 most recent transactions across all of this user’s accounts
    recent_transactions = (
        Transaction.objects
        .filter(account__in=accounts)
        .order_by('-timestamp')[:5]
    )

    context = {
        'accounts': accounts,
        'total_balance': total_balance,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'bdounibank/dashboard.html', context)

@login_required
def account_list_view(request):
    accounts = BankAccount.objects.filter(owner=request.user)
    return render(request, 'bdounibank/account_list.html', {'accounts': accounts})

@login_required
def account_detail_view(request, account_number):
    account = get_object_or_404(BankAccount, account_number=account_number)
    
    # Ensure the account belongs to the current user
    if account.owner != request.user and not request.user.user_type in ['staff', 'admin']:
        return HttpResponseForbidden("You don't have permission to view this account.")
    
    # Get transactions for this account
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:20]
    
    context = {
        'account': account,
        'transactions': transactions
    }
    return render(request, 'bdounibank/account_detail.html', context)

@login_required
def create_account_view(request):
    if request.method == 'POST':
        form = BankAccountCreationForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.owner = request.user
            # Generate unique account number
            account.account_number = f"BDO-{uuid.uuid4().hex[:10].upper()}"
            account.save()
            
            # Process initial deposit
            # initial_deposit = form.cleaned_data['initial_deposit']
            # account.deposit(initial_deposit)
            
            # Create transaction record
            # Transaction.objects.create(
            #     account=account,
            #     transaction_type='deposit',
            #     amount=initial_deposit,
            #     status='completed',
            #     description='Initial deposit'
            # )
            
            # messages.success(request, f"Account created successfully with an initial deposit of {initial_deposit}.")
            messages.success(request, f"Account created successfully.")
            return redirect('account_detail', account_number=account.account_number)
    else:
        form = BankAccountCreationForm()
    
    account_types = AccountType.objects.all()
    context = {
        'form': form,
        'account_types': account_types
    }
    return render(request, 'bdounibank/create_account.html', context)



from django.shortcuts import render

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)