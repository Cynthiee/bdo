# transactions/views.py
from __future__ import annotations

import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_txn
from django.shortcuts import get_object_or_404, redirect, render

from bdounibank.models import BankAccount
from .forms import (
    CodeVerificationForm,
    DepositForm,
    TransferForm,
    TransferRequestForm,
    WithdrawalForm,
    WithdrawalRequestForm,
)
from .models import COTCode, IMFCode, Transaction, Transfer, VerificationLog

MAX_ATTEMPTS = 3
ORDER_FIELD = "timestamp" if hasattr(Transaction, "timestamp") else "created_at"

# ------------------------------------------------------------------
# 1.  History  (user‑scoped)
# ------------------------------------------------------------------
@login_required
def transaction_history_view(request):
    """Show all transactions that belong to the signed‑in user."""
    qs = Transaction.objects.filter(user=request.user).order_by(f"-{ORDER_FIELD}")

    if acc := request.GET.get("account"):
        qs = qs.filter(account__account_number=acc)
    if typ := request.GET.get("type"):
        qs = qs.filter(transaction_type=typ)
    if frm := request.GET.get("date_from"):
        qs = qs.filter(**{f"{ORDER_FIELD}__gte": frm})
    if to := request.GET.get("date_to"):
        qs = qs.filter(**{f"{ORDER_FIELD}__lte": to})

    user_accounts = BankAccount.objects.filter(owner=request.user)
    return render(
        request,
        "transactions/history.html",
        {"transactions": qs, "accounts": user_accounts},
    )


# ------------------------------------------------------------------
# 2.  Deposit  (no IMF/COT)
# ------------------------------------------------------------------
@login_required
def deposit_view(request):
    form = DepositForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        acc = form.cleaned_data["account"]
        amt = form.cleaned_data["amount"]
        desc = form.cleaned_data.get("description") or "Deposit request"

        Transaction.objects.create(
            user=request.user,
            account=acc,
            transaction_type="deposit",
            amount=amt,
            status="pending",
            description=desc,
        )
        messages.success(request, f"Deposit of ${amt} submitted for admin approval.")
        return redirect("account_detail", account_number=acc.account_number)

    return render(request, "transactions/deposit.html", {"form": form})


# ------------------------------------------------------------------
# 3.  Withdrawal Request  → IMF/COT chain
# ------------------------------------------------------------------
@login_required
def withdrawal_request(request):
    form = WithdrawalRequestForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        txn: Transaction = form.save(commit=False)
        txn.user = request.user
        txn.transaction_type = "withdrawal"
        txn.save()
        return redirect("verify_imf", transaction_id=txn.transaction_id)

    return render(request, "transactions/withdrawal_form.html", {"form": form})


# ------------------------------------------------------------------
# 4.  Transfer Request  → IMF/COT chain
# ------------------------------------------------------------------
@login_required
def transfer_request(request):
    form = TransferRequestForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        txn: Transaction = form.save(commit=False)
        txn.user = request.user
        txn.transaction_type = "transfer"
        txn.save()  # generates UUID pk
        return redirect("verify_imf", transaction_id=txn.transaction_id)

    return render(request, "transactions/transfer_form.html", {"form": form})


# ------------------------------------------------------------------
# 5.  Instant transfer  (legacy / optional)
# ------------------------------------------------------------------
@login_required
def transfer_view(request):
    form = TransferForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        src = form.cleaned_data["source_account"]
        dst = form.cleaned_data["destination_account"]
        amt = form.cleaned_data["amount"]
        desc = form.cleaned_data.get("description") or f"Transfer to {dst.account_number}"

        if dst.owner == request.user and dst != src:
            messages.error(request, "Instant transfer cannot target another of your own accounts.")
            return redirect("transfer")

        with db_txn.atomic():
            src.withdraw(amt)
            dst.deposit(amt)

            ref = uuid.uuid4()
            src_txn = Transaction.objects.create(
                transaction_id=ref,
                user=request.user,
                account=src,
                transaction_type="transfer",
                amount=amt,
                status="completed",
                description=desc,
                reference_number=str(ref),
            )
            Transaction.objects.create(
                user=request.user,
                account=dst,
                transaction_type="transfer",
                amount=amt,
                status="completed",
                description=f"Transfer from {src.account_number}",
                reference_number=str(ref),
            )
            Transfer.objects.create(
                transaction=src_txn, source_account=src, destination_account=dst
            )

        messages.success(request, f"Transfer of ${amt} completed.")
        return redirect("account_detail", account_number=src.account_number)

    return render(request, "transactions/transfer.html", {"form": form})


# ------------------------------------------------------------------
# 6.  IMF verification
# ------------------------------------------------------------------
@login_required
def verify_imf(request, transaction_id):
    txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    if txn.is_imf_verified:
        return redirect("verify_cot", transaction_id=txn.transaction_id)

    error = None
    form = CodeVerificationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"].strip()
        txn.imf_attempts += 1
        txn.save()

        if txn.imf_attempts > MAX_ATTEMPTS:
            error = "Too many incorrect attempts. Contact support."
        else:
            try:
                code_obj = IMFCode.objects.get(code=code, active=True)
            except IMFCode.DoesNotExist:
                error = "Invalid IMF code."
            else:
                txn.is_imf_verified = True
                txn.save()
                code_obj.usage_count += 1
                code_obj.save()

                VerificationLog.objects.create(
                    user=request.user,
                    transaction=txn,
                    code_type="IMF",
                    code_value=code,
                    success=True,
                )
                return redirect("verify_cot", transaction_id=txn.transaction_id)

    return render(request, "transactions/verify_imf.html", {"form": form, "error": error})


# ------------------------------------------------------------------
# 7.  COT verification
# ------------------------------------------------------------------
@login_required
def verify_cot(request, transaction_id):
    txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    if not txn.is_imf_verified:
        return redirect("verify_imf", transaction_id=txn.transaction_id)
    if txn.is_cot_verified:
        return redirect("verify_step1", transaction_id=txn.transaction_id)

    error = None
    form = CodeVerificationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"].strip()
        txn.cot_attempts += 1
        txn.save()

        if txn.cot_attempts > MAX_ATTEMPTS:
            error = "Too many incorrect attempts. Contact support."
        else:
            try:
                code_obj = COTCode.objects.get(code=code, active=True)
            except COTCode.DoesNotExist:
                error = "Invalid COT code."
            else:
                txn.is_cot_verified = True
                txn.save()
                code_obj.usage_count += 1
                code_obj.save()

                VerificationLog.objects.create(
                    user=request.user,
                    transaction=txn,
                    code_type="COT",
                    code_value=code,
                    success=True,
                )
                return redirect("verify_step1", transaction_id=txn.transaction_id)

    return render(request, "transactions/verify_cot.html", {"form": form, "error": error})


# ------------------------------------------------------------------
# 8.  Final three confirmation steps
# ------------------------------------------------------------------
@login_required
def verify_step1(request, transaction_id):
    txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    if not (txn.is_imf_verified and txn.is_cot_verified):
        return redirect("transfer_request")

    if request.method == "POST":
        txn.step1_done = True
        txn.save()
        return redirect("verify_step2", transaction_id=txn.transaction_id)

    return render(request, "transactions/verify_step.html", {"step": 1})


@login_required
def verify_step2(request, transaction_id):
    txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    if not txn.step1_done:
        return redirect("verify_step1", transaction_id=txn.transaction_id)

    if request.method == "POST":
        txn.step2_done = True
        txn.save()
        return redirect("verify_step3", transaction_id=txn.transaction_id)

    return render(request, "transactions/verify_step.html", {"step": 2})


@login_required
def verify_step3(request, transaction_id):
    txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    if not txn.step2_done:
        return redirect("verify_step2", transaction_id=txn.transaction_id)

    if request.method == "POST":
        txn.step3_done = True
        txn.completed = True
        txn.save()
        return redirect("verify_complete", transaction_id=txn.transaction_id)

    return render(request, "transactions/verify_step.html", {"step": 3})


@login_required
def verify_complete(request, transaction_id):
    txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    if not txn.completed:
        return redirect("transfer_request")
    return render(request, "transactions/verify_complete.html", {"transaction": txn})
