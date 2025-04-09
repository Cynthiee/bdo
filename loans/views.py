from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Loan, LoanPayment, LoanType
from .forms import LoanApplicationForm, LoanPaymentForm
from transactions.models import Transaction
import uuid

@login_required
def loan_list_view(request):
    loans = Loan.objects.filter(borrower=request.user)
    return render(request, 'loans/loan_list.html', {'loans': loans})

@login_required
def loan_detail_view(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    
    # Ensure the loan belongs to the current user
    if loan.borrower != request.user and not request.user.user_type in ['staff', 'admin']:
        return HttpResponseForbidden("You don't have permission to view this loan.")
    
    # Get payments for this loan
    payments = LoanPayment.objects.filter(loan=loan).order_by('-payment_date')
    
    context = {
        'loan': loan,
        'payments': payments
    }
    return render(request, 'loans/loan_detail.html', context)

@login_required
def loan_application_view(request):
    if request.method == 'POST':
        form = LoanApplicationForm(request.user, request.POST)
        if form.is_valid():
            loan = form.save()
            messages.success(request, "Loan application submitted successfully. It is now pending approval.")
            return redirect('loan_detail', loan_id=loan.loan_id)
    else:
        form = LoanApplicationForm(request.user)
    
    loan_types = LoanType.objects.all()
    context = {
        'form': form,
        'loan_types': loan_types
    }
    return render(request, 'loans/loan_application.html', context)

@login_required
def loan_payment_view(request):
    if request.method == 'POST':
        form = LoanPaymentForm(request.user, request.POST)
        if form.is_valid():
            loan = form.cleaned_data['loan']
            payment_amount = form.cleaned_data['payment_amount']
            payment_account = form.cleaned_data['payment_account']
            
            # Process loan payment
            with transaction.atomic():
                # Withdraw from payment account
                payment_account.withdraw(payment_amount)
                
                # Calculate principal and interest components
                # For simplicity, we're using a basic calculation
                # A more complex amortization schedule would be used in a real application
                monthly_interest = (loan.interest_rate / 100 / 12) * loan.amount
                if payment_amount <= monthly_interest:
                    interest_component = payment_amount
                    principal_component = 0
                else:
                    interest_component = monthly_interest
                    principal_component = payment_amount - interest_component
                
                # Create transaction record
                transaction_record = Transaction.objects.create(
                    account=payment_account,
                    transaction_type='loan_payment',
                    amount=payment_amount,
                    status='completed',
                    description=f'Loan payment for loan {loan.loan_id}'
                )
                
                # Create loan payment record
                LoanPayment.objects.create(
                    loan=loan,
                    amount=payment_amount,
                    principal_component=principal_component,
                    interest_component=interest_component,
                    transaction=transaction_record
                )
                
                messages.success(request, f"Loan payment of {payment_amount} processed successfully.")
                return redirect('loan_detail', loan_id=loan.loan_id)
    else:
        form = LoanPaymentForm(request.user)
    
    return render(request, 'loans/loan_payment.html', {'form': form})