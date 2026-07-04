from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser
from apps.courses.models import Enrollment
from .managers import PaymentQuerySet


# ─── Pagos ────────────────────────────────────────────────────────────────────

class Payment(models.Model):
    class Method(models.TextChoices):
        CASH         = 'cash',         _('Efectivo')
        TRANSFER     = 'transfer',     _('Transferencia')
        CREDIT_CARD  = 'credit_card',  _('Tarjeta crédito')
        DEBIT_CARD   = 'debit_card',   _('Tarjeta débito')
        OTHER        = 'other',        _('Otro')

    class Status(models.TextChoices):
        PENDING   = 'pending',   _('Pendiente')
        CONFIRMED = 'confirmed', _('Confirmado')
        REJECTED  = 'rejected',  _('Rechazado')
        REFUNDED  = 'refunded',  _('Reembolsado')

    enrollment       = models.ForeignKey(Enrollment, on_delete=models.PROTECT, related_name='payments')
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method   = models.CharField(max_length=20, choices=Method.choices)
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_date     = models.DateField()
    reference_number = models.CharField(max_length=100, blank=True)
    notes            = models.TextField(blank=True)
    recorded_by      = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True,
        related_name='payments_recorded'
    )
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    objects = PaymentQuerySet.as_manager()

    class Meta:
        verbose_name = _('Pago')
        verbose_name_plural = _('Pagos')
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['enrollment', 'status']),
        ]

    def __str__(self):
        return f"Pago #{self.pk} – {self.enrollment.student.full_name} – {self.amount}"


# ─── Facturas ─────────────────────────────────────────────────────────────────

def invoice_pdf_path(instance, filename):
    return f"invoices/{instance.payment.enrollment.course.code}/{filename}"


class Invoice(models.Model):
    class SentStatus(models.TextChoices):
        PENDING = 'pending', _('Pendiente')
        SENT    = 'sent',    _('Enviada')
        FAILED  = 'failed',  _('Fallida')

    payment          = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name='invoice')
    invoice_number   = models.CharField(max_length=50, unique=True)
    pdf_file         = models.FileField(upload_to=invoice_pdf_path, blank=True, null=True)
    issued_at        = models.DateTimeField(auto_now_add=True)
    sent_status      = models.CharField(max_length=20, choices=SentStatus.choices, default=SentStatus.PENDING)
    sent_at          = models.DateTimeField(null=True, blank=True)
    recipient_email  = models.EmailField()

    class Meta:
        verbose_name = _('Factura')
        verbose_name_plural = _('Facturas')
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['sent_status', 'issued_at']),
        ]

    def __str__(self):
        return f"Factura {self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from django.utils import timezone
            year = timezone.now().year
            last = Invoice.objects.filter(
                invoice_number__startswith=f"EF-{year}-"
            ).order_by('-invoice_number').first()
            seq = int(last.invoice_number.split('-')[-1]) + 1 if last else 1
            self.invoice_number = f"EF-{year}-{seq:05d}"
        super().save(*args, **kwargs)


# ─── Log de emails ────────────────────────────────────────────────────────────

class EmailLog(models.Model):
    class Status(models.TextChoices):
        QUEUED  = 'queued',  _('En cola')
        SENT    = 'sent',    _('Enviado')
        FAILED  = 'failed',  _('Fallido')

    invoice       = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='email_logs')
    recipient     = models.EmailField()
    subject       = models.CharField(max_length=200)
    status        = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    sent_at       = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Log de email')
        verbose_name_plural = _('Logs de email')
        ordering = ['-created_at']

    def __str__(self):
        return f"Email {self.invoice.invoice_number} → {self.recipient} [{self.get_status_display()}]"
