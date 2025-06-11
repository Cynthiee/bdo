import logging
import tempfile
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import now

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
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
            HTML(string=html_string).write_pdf(tmp.name)
            tmp.seek(0)
            return tmp.read()
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None


def send_transaction_email_with_receipt(transaction):
    user = transaction.account.owner
    if not user.email:
        logger.warning(f"No email set for user: {user.username}")
        return

    subject = f"{transaction.transaction_type.title()} Notification - ₦{transaction.amount}"
    from_email = 'noreply@yourbank.com'
    to_email = user.email

    # Plain text content
    text_content = (
        f"{transaction.transaction_type.title()} of ₦{transaction.amount} processed.\n"
        f"New balance: ₦{transaction.account.balance:.2f}\n"
        f"Date: {transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "If unauthorized, contact support."
    )

    # HTML content
    html_content = render_to_string('email/transaction_email.html', {
        'username': user.username,
        'transaction_type': transaction.transaction_type,
        'amount': f"{transaction.amount:.2f}",
        'balance': f"{transaction.account.balance:.2f}",
        'description': transaction.description or '',
        'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'current_year': now().year
    })

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")

    # Attach PDF if available
    pdf_bytes = generate_pdf_receipt(transaction)
    if pdf_bytes:
        filename = f"receipt_{transaction.transaction_id}.pdf"
        email.attach(filename, pdf_bytes, 'application/pdf')
    else:
        logger.info("No PDF attached to email (PDF generation skipped or failed).")

    try:
        email.send()
        logger.info(f"Transaction email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send transaction email: {e}")
