from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from bdounibank.models import BankAccount
from django.db import transaction as db_transaction
from .models import Transaction, Transfer
from .forms import DepositForm, WithdrawalForm, TransferForm
import uuid

@login_required
def transaction_history_view(request):
    # Get all accounts owned by the user
    accounts = BankAccount.objects.filter(owner=request.user)
    
    # Get all transactions for these accounts
    transactions = Transaction.objects.filter(account__in=accounts).order_by('-timestamp')
    
    # Handle filtering
    account_filter = request.GET.get('account')
    transaction_type = request.GET.get('type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if account_filter:
        transactions = transactions.filter(account__account_number=account_filter)
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if date_from:
        transactions = transactions.filter(timestamp__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(timestamp__lte=date_to)
    
    context = {
        'transactions': transactions,
        'accounts': accounts
    }
    return render(request, 'transactions/history.html', context)

@login_required
def deposit_view(request):
    if request.method == 'POST':
        form = DepositForm(request.user, request.POST)
        if form.is_valid():
            account = form.cleaned_data['account']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description') or 'Deposit request'
            # Create a pending transaction for admin review
            Transaction.objects.create(
                account=account,
                transaction_type='deposit',
                amount=amount,
                status='pending',
                description=description
            )
            messages.success(request, f"Deposit of ₦{amount} submitted and is pending admin approval.")
            return redirect('account_detail', account_number=account.account_number)
    else:
        form = DepositForm(request.user)
    return render(request, 'transactions/deposit.html', {'form': form})

@login_required
def withdrawal_view(request):
    if request.method == 'POST':
        form = WithdrawalForm(request.user, request.POST)
        if form.is_valid():
            account = form.cleaned_data['account']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description') or 'Withdrawal request'
            # Create a pending transaction for admin review
            Transaction.objects.create(
                account=account,
                transaction_type='withdrawal',
                amount=amount,
                status='pending',
                description=description
            )
            messages.success(request, f"Withdrawal of ₦{amount} submitted and is pending admin approval.")
            return redirect('account_detail', account_number=account.account_number)
    else:
        form = WithdrawalForm(request.user)
    return render(request, 'transactions/withdrawal.html', {'form': form})


@login_required
def transfer_view(request):
    if request.method == 'POST':
        form = TransferForm(request.user, request.POST)
        if form.is_valid():
            source_account = form.cleaned_data['source_account']
            destination_account = form.cleaned_data['destination_account']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description') or f'Transfer to {destination_account.account_number}'
            
            with db_transaction.atomic():
                # Withdraw from source; may raise if insufficient
                source_account.withdraw(amount)
                # Deposit to destination
                destination_account.deposit(amount)
                
                # Use a common reference for both sides
                ref = uuid.uuid4()
                
                # Source transaction
                source_transaction = Transaction.objects.create(
                    transaction_id=ref,
                    account=source_account,
                    transaction_type='transfer',
                    amount=amount,
                    status='completed',
                    description=description,
                    reference_number=str(ref)
                )
                # Destination transaction
                Transaction.objects.create(
                    account=destination_account,
                    transaction_type='transfer',
                    amount=amount,
                    status='completed',
                    description=f'Transfer from {source_account.account_number}',
                    reference_number=str(ref)
                )
                # Record Transfer link
                Transfer.objects.create(
                    transaction=source_transaction,
                    source_account=source_account,
                    destination_account=destination_account
                )
            messages.success(request, f"Transfer of ₦{amount} completed successfully.")
            return redirect('account_detail', account_number=source_account.account_number)
    else:
        form = TransferForm(request.user)
    return render(request, 'transactions/transfer.html', {'form': form})

