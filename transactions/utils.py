import logging
import tempfile
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import now
import os
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None


logger = logging.getLogger(__name__)

def generate_pdf_receipt(transaction):
    """
    Render receipt HTML and convert to PDF bytes.
    """
    if not WEASYPRINT_AVAILABLE:
        logger.warning("WeasyPrint not available. Skipping PDF generation.")
        return None

    context = {
        'transaction_id': transaction.transaction_id,
        'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'account_number': transaction.account.account_number,
        'username': transaction.account.owner.username,
        'transaction_type': transaction.transaction_type,
        'amount': f"{transaction.amount:.2f}",
        'balance': f"{transaction.account.balance:.2f}",
        'description': transaction.description or '',
        'current_year': now().year,
    }

    html_string = render_to_string('pdf/receipt.html', context)

    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            HTML(string=html_string).write_pdf(tmp.name)
            tmp.seek(0)
            pdf_data = tmp.read()
        os.unlink(tmp.name)
        return pdf_data
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None
    


def send_transaction_email_with_receipt(transaction):
    """
    Sends an email to the user for a completed transaction,
    optionally with a PDF receipt.
    """
    user = getattr(transaction.account, 'owner', None)
    if not user or not user.email:
        logger.warning("No valid user or user email for transaction ID %s", transaction.transaction_id)
        return

    try:
        subject = f"{transaction.transaction_type.title()} Notification - ${transaction.amount:.2f}"
        from_email = 'noreply@mainwesthern.com'
        to_email = user.email

        context = {
            'username': user.username,
            'transaction_type': transaction.transaction_type,
            'amount': f"{transaction.amount:.2f}",
            'balance': f"{transaction.account.balance:.2f}",
            'description': transaction.description or '',
            'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'current_year': now().year,
        }

        text_content = (
            f"{transaction.transaction_type.title()} of ${transaction.amount:.2f} processed.\n"
            f"New balance: ${transaction.account.balance:.2f}\n"
            f"Date: {context['timestamp']}\n"
            "If unauthorized, contact support."
        )

        html_content = render_to_string('email/transaction_email.html', context)

        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")

        # Attach PDF receipt if generated
        pdf_bytes = generate_pdf_receipt(transaction)
        if pdf_bytes:
            email.attach(f"receipt_{transaction.transaction_id}.pdf", pdf_bytes, 'application/pdf')
            logger.debug("PDF receipt attached for transaction ID %s", transaction.transaction_id)

        email.send()
        logger.info("Transaction email sent to %s for transaction ID %s", to_email, transaction.transaction_id)

    except Exception as e:
        logger.exception("Failed to send transaction email for transaction ID %s", transaction.transaction_id)
