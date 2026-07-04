from django.http import FileResponse, Http404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.models import CustomUser
from .models import Payment, Invoice
from .serializers import PaymentSerializer, InvoiceSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows payments to be viewed or registered.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.Role.STUDENT:
            return Payment.objects.filter(enrollment__student=user).select_related('enrollment__course').order_by('-payment_date')
        else:
            return Payment.objects.all().select_related('enrollment__student', 'enrollment__course', 'recorded_by').order_by('-payment_date')

    def perform_create(self, serializer):
        # Default recorder is current user
        serializer.save(recorded_by=self.request.user)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows invoices to be viewed and downloaded.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.Role.STUDENT:
            return Invoice.objects.filter(payment__enrollment__student=user).select_related('payment').order_by('-issued_at')
        else:
            return Invoice.objects.all().select_related('payment').order_by('-issued_at')

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        """
        Download the official invoice file: /api/invoices/{id}/pdf/
        """
        invoice = self.get_object()
        
        # Verify access permission for students
        if request.user.role == CustomUser.Role.STUDENT and invoice.payment.enrollment.student != request.user:
            return Response(
                {"detail": "No tienes permiso para descargar esta factura."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if not invoice.pdf_file:
            return Response(
                {"detail": "El archivo de factura no ha sido generado todavía o el procesamiento falló."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Try to open and send the file
        try:
            file_handle = invoice.pdf_file.open()
            
            # Determine content type based on extension (handling our HTML fallback)
            ext = invoice.pdf_file.name.split('.')[-1].lower()
            content_type = 'application/pdf' if ext == 'pdf' else 'text/html'
            
            response = FileResponse(file_handle, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{invoice.pdf_file.name.split("/")[-1]}"'
            return response
        except FileNotFoundError:
            raise Http404("Archivo físico no encontrado.")
