import os
import logging
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from .models import Invoice, EmailLog

logger = logging.getLogger(__name__)


@shared_task
def process_invoice_generation_and_email(invoice_id):
    """
    Background Celery task that:
    1. Generates the PDF (or fallback HTML) for the invoice using WeasyPrint.
    2. Saves the file to the invoice model.
    3. Sends an email to the recipient with the file attached.
    4. Logs the email status in EmailLog.
    """
    try:
        invoice = Invoice.objects.select_related('payment__enrollment__student', 'payment__enrollment__course').get(pk=invoice_id)
    except Invoice.DoesNotExist:
        logger.error(f"Invoice with id {invoice_id} does not exist.")
        return

    # Create Email Log as queued
    email_log = EmailLog.objects.create(
        invoice=invoice,
        recipient=invoice.recipient_email,
        subject=f"Factura de Pago {invoice.invoice_number} — EduFlow",
        status=EmailLog.Status.QUEUED
    )

    # 1. Render HTML
    html_content = render_to_string('invoices/invoice_pdf.html', {'invoice': invoice})
    
    file_data = None
    file_ext = ""
    content_type = ""
    
    # 2. Attempt PDF generation using WeasyPrint
    try:
        from weasyprint import HTML
        logger.info(f"Generating PDF for invoice {invoice.invoice_number} using WeasyPrint...")
        pdf_bytes = HTML(string=html_content).write_pdf()
        file_data = pdf_bytes
        file_ext = "pdf"
        content_type = "application/pdf"
    except Exception as e:
        # Fallback to HTML if WeasyPrint C-libraries (Pango/Cairo) are missing on Windows
        logger.warning(
            f"WeasyPrint PDF generation failed due to: {e}. "
            f"Falling back to HTML file attachment."
        )
        file_data = html_content.encode('utf-8')
        file_ext = "html"
        content_type = "text/html"

    # 3. Save file to the invoice model
    filename = f"factura_{invoice.invoice_number}.{file_ext}"
    invoice.pdf_file.save(filename, ContentFile(file_data), save=False)
    invoice.sent_status = Invoice.SentStatus.PENDING
    invoice.save()

    # 4. Send Email with attachment
    try:
        subject = f"Factura de Pago {invoice.invoice_number} — EduFlow"
        body = f"""Hola {invoice.payment.enrollment.student.first_name},
        
Hemos confirmado tu pago de ${invoice.payment.amount} para el curso {invoice.payment.enrollment.course.name}.
Adjunto encontrarás la factura oficial correspondiente en formato {file_ext.upper()}.

Gracias por estudiar con nosotros.
El Equipo de EduFlow
"""
        
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.recipient_email]
        )
        
        # Attach file
        email.attach(filename, file_data, content_type)
        
        # Send email
        logger.info(f"Sending invoice email to {invoice.recipient_email}...")
        email.send(fail_silently=False)
        
        # Update Invoice and Email Log as Sent
        invoice.sent_status = Invoice.SentStatus.SENT
        invoice.sent_at = timezone.now()
        invoice.save()
        
        email_log.status = EmailLog.Status.SENT
        email_log.sent_at = timezone.now()
        email_log.save()
        
        logger.info(f"Invoice {invoice.invoice_number} processed and sent successfully.")
        
    except Exception as email_err:
        logger.error(f"Failed to send email for invoice {invoice.invoice_number}: {email_err}")
        
        # Update status to failed
        invoice.sent_status = Invoice.SentStatus.FAILED
        invoice.save()
        
        email_log.status = EmailLog.Status.FAILED
        email_log.error_message = str(email_err)
        email_log.save()
