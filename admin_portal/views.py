from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction, models as django_models
from django.utils import timezone
from django.core.paginator import Paginator
from accounts import models
from accounts.models import User, CustomerProfile
from bdounibank.models import BankAccount, AccountType
from loans.models import Loan, LoanType
from transactions.models import Transaction
from .models import AuditLog, SystemSetting
from django.db.models import Q
from .forms import UserSearchForm, AccountSearchForm, LoanApprovalForm, BankAccountForm

# Helper function to check if user is admin or staff
def is_admin_or_staff(user):
    return user.user_type in ['admin', 'staff']

@login_required
# @user_passes_test(is_admin_or_staff)
def admin_dashboard_view(request):
    # Get counts for dashboard
    user_count = User.objects.filter(user_type='customer').count()
    account_count = BankAccount.objects.count()
    active_loans_count = Loan.objects.filter(status='active').count()
    pending_loans_count = Loan.objects.filter(status='pending').count()
    
    # Get recent transactions
    recent_transactions = Transaction.objects.order_by('-timestamp')[:10]
    
    # Get recent audit logs
    recent_audit_logs = AuditLog.objects.order_by('-timestamp')[:10]
    
    context = {
        'user_count': user_count,
        'account_count': account_count,
        'active_loans_count': active_loans_count,
        'pending_loans_count': pending_loans_count,
        'recent_transactions': recent_transactions,
        'recent_audit_logs': recent_audit_logs
    }
    return render(request, 'admin_portal/dashboard.html', context)

@login_required
# @user_passes_test(is_admin_or_staff)
def user_management_view(request):
    form = UserSearchForm(request.GET)
    users = User.objects.all()
    
    if form.is_valid():
        search_term = form.cleaned_data.get('search_term')
        user_type = form.cleaned_data.get('user_type')
        status = form.cleaned_data.get('status')
        
        if search_term:
            users = users.filter(
            django_models.Q(username__icontains=search_term) |
            django_models.Q(email__icontains=search_term) |
            django_models.Q(first_name__icontains=search_term) |
            django_models.Q(last_name__icontains=search_term)
    )
        
        if user_type:
            users = users.filter(user_type=user_type)
        
        if status:
            users = users.filter(is_active=(status == 'active'))
    
    # Paginate results
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_portal/user_management.html', {
        'form': form,
        'page_obj': page_obj
    })

@login_required
@user_passes_test(is_admin_or_staff)
def account_management_view(request):
    form = AccountSearchForm(request.GET)
    accounts = BankAccount.objects.all()
    
    if form.is_valid():
        search_term = form.cleaned_data.get('search_term')
        account_status = form.cleaned_data.get('account_status')
        
        if search_term:
            accounts = accounts.filter(
                Q(account_number__icontains=search_term) |
                Q(owner__username__icontains=search_term) |
                Q(owner__email__icontains=search_term)
            )
        
        if account_status:
            accounts = accounts.filter(status=account_status)
    
    # Paginate results
    paginator = Paginator(accounts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_portal/account_management.html', {
        'form': form,
        'page_obj': page_obj
    })

@login_required
@user_passes_test(is_admin_or_staff)
def loan_management_view(request):
    # Get loans with different statuses
    pending_loans = Loan.objects.filter(status='pending')
    active_loans = Loan.objects.filter(status='active')
    closed_loans = Loan.objects.filter(status__in=['paid', 'closed', 'rejected', 'defaulted'])
    
    context = {
        'pending_loans': pending_loans,
        'active_loans': active_loans,
        'closed_loans': closed_loans
    }
    return render(request, 'admin_portal/loan_management.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def loan_approval_view(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    
    if loan.status != 'pending':
        messages.error(request, "This loan is not pending approval.")
        return redirect('loan_management')
    
    if request.method == 'POST':
        form = LoanApprovalForm(loan_id, request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            notes = form.cleaned_data['notes']
            
            with transaction.atomic():
                if decision == 'approve':
                    loan.status = 'approved'
                    loan.approval_date = timezone.now()
                    
                    # Calculate payment dates
                    loan.disbursal_date = timezone.now()
                    loan.next_payment_date = loan.disbursal_date.date().replace(day=1) + timezone.timedelta(days=32)
                    loan.next_payment_date = loan.next_payment_date.replace(day=1)  # First day of next month
                    
                    loan.final_payment_date = loan.next_payment_date
                    for _ in range(loan.term_months - 1):
                        loan.final_payment_date = loan.final_payment_date.replace(day=1) + timezone.timedelta(days=32)
                        loan.final_payment_date = loan.final_payment_date.replace(day=1)
                    
                    # Disburse loan amount to linked account
                    loan.linked_account.deposit(loan.amount)
                    
                    # Create transaction record
                    Transaction.objects.create(
                        account=loan.linked_account,
                        transaction_type='deposit',
                        amount=loan.amount,
                        status='completed',
                        description=f'Loan disbursement for loan {loan.loan_id}'
                    )
                    
                    messages.success(request, f"Loan {loan.loan_id} has been approved and disbursed.")
                else:
                    loan.status = 'rejected'
                    messages.success(request, f"Loan {loan.loan_id} has been rejected.")
                
                loan.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='approve' if decision == 'approve' else 'reject',
                    resource_type='Loan',
                    resource_id=str(loan.loan_id),
                    details=notes
                )
                
            return redirect('loan_management')
    else:
        form = LoanApprovalForm(loan_id)
    
    context = {
        'form': form,
        'loan': loan
    }
    return render(request, 'admin_portal/loan_approval.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def audit_log_view(request):
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    # Paginate results
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_portal/audit_logs.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_admin_or_staff)
def system_settings_view(request):
    settings = SystemSetting.objects.all()
    
    if request.method == 'POST':
        # Update settings
        for setting in settings:
            new_value = request.POST.get(f'setting_{setting.id}')
            if new_value and new_value != setting.value:
                setting.value = new_value
                setting.modified_by = request.user
                setting.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    resource_type='SystemSetting',
                    resource_id=setting.key,
                    details=f'Changed value from {setting.value} to {new_value}'
                )
        
        messages.success(request, "Settings updated successfully.")
        return redirect('system_settings')
    
    return render(request, 'admin_portal/system_settings.html', {'settings': settings})

@login_required
@user_passes_test(is_admin_or_staff)
def user_detail_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    customer_profile = None
    bank_accounts = None
    loans = None
    
    if user.user_type == 'customer':
        customer_profile = CustomerProfile.objects.filter(user=user).first()
        bank_accounts = BankAccount.objects.filter(owner=user)
        loans = Loan.objects.filter(borrower=user)
    
    context = {
        'user_obj': user,
        'customer_profile': customer_profile,
        'bank_accounts': bank_accounts,
        'loans': loans,
    }
    return render(request, 'admin_portal/user_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def user_edit_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Basic user info updates
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        
        # Status updates
        is_active = request.POST.get('is_active') == 'on'
        if user.is_active != is_active:
            user.is_active = is_active
            
            # Create audit log for status change
            AuditLog.objects.create(
                user=request.user,
                action='update',
                resource_type='User',
                resource_id=str(user.id),
                details=f'Changed user status to {"active" if is_active else "inactive"}'
            )
        
        user.save()
        messages.success(request, f"User {user.username} has been updated.")
        return redirect('user_detail', user_id=user.id)
    
    context = {
        'user_obj': user,
    }
    return render(request, 'admin_portal/user_edit.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def account_detail_view(request, account_id):
    account = get_object_or_404(BankAccount, id=account_id)
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:20]
    
    # Paginate transactions
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'account': account,
        'page_obj': page_obj,
    }
    return render(request, 'admin_portal/account_detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def account_edit_view(request, account_id):
    """
    Let an admin/staff edit all fields of a BankAccount.
    """
    account = get_object_or_404(BankAccount, id=account_id)

    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            # After saving, redirect back to the account detail page:
            return redirect('account_detail', account_id=account.id)
    else:
        form = BankAccountForm(instance=account)

    return render(request, 'admin_portal/edit_account.html', {
        'bank_account': account,
        'form': form,
    })