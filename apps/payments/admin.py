from django.contrib import admin
from .models import Payment, Invoice, EmailLog


class InvoiceInline(admin.StackedInline):
    model     = Invoice
    extra     = 0
    readonly_fields = ('invoice_number', 'issued_at', 'sent_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ('id', 'enrollment', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter   = ('status', 'payment_method')
    search_fields = ('enrollment__student__username', 'reference_number')
    inlines       = [InvoiceInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ('invoice_number', 'payment', 'sent_status', 'issued_at', 'sent_at')
    list_filter   = ('sent_status',)
    search_fields = ('invoice_number', 'recipient_email')
    readonly_fields = ('invoice_number', 'issued_at')


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'recipient', 'status', 'sent_at')
    list_filter  = ('status',)
