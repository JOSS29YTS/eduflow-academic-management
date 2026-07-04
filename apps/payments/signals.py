from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment, Invoice
from .tasks import process_invoice_generation_and_email


@receiver(post_save, sender=Payment)
def auto_create_invoice_on_confirmed_payment(sender, instance, created, **kwargs):
    """
    When a Payment status changes to CONFIRMED, automatically generate the associated Invoice.
    """
    if instance.status == Payment.Status.CONFIRMED:
        # Check if invoice already exists
        if not hasattr(instance, 'invoice'):
            Invoice.objects.create(
                payment=instance,
                recipient_email=instance.enrollment.student.email,
                sent_status=Invoice.SentStatus.PENDING
            )


@receiver(post_save, sender=Invoice)
def trigger_celery_task_on_new_invoice(sender, instance, created, **kwargs):
    """
    When a new Invoice is created, queue the Celery task to generate PDF and send email.
    """
    if created:
        # Queue task asynchronously via Celery (runs synchronously in dev due to eager setting)
        process_invoice_generation_and_email.delay(instance.id)
