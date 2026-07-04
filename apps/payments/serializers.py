from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.courses.serializers import EnrollmentSerializer
from apps.courses.models import Enrollment
from .models import Payment, Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ('id', 'invoice_number', 'pdf_file', 'issued_at', 'sent_status', 'sent_at', 'recipient_email')
        read_only_fields = ('id', 'invoice_number', 'pdf_file', 'issued_at', 'sent_status', 'sent_at')


class PaymentSerializer(serializers.ModelSerializer):
    enrollment = EnrollmentSerializer(read_only=True)
    enrollment_id = serializers.PrimaryKeyRelatedField(
        queryset=Enrollment.objects.all(), source='enrollment', write_only=True
    )
    invoice = InvoiceSerializer(read_only=True)
    recorded_by = UserSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'enrollment', 'enrollment_id', 'amount', 'payment_method', 
            'status', 'payment_date', 'reference_number', 'notes', 'recorded_by', 'invoice'
        )
        read_only_fields = ('id', 'status', 'recorded_by')
