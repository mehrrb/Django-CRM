from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import EmailMessage

from invoices.models import Invoice
from invoices.serializers import InvoiceSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def send_mail(self, request, pk=None):
        invoice = self.get_object()
        subject = f'Invoice #{invoice.invoice_number}'
        message = f"""
        Invoice Details:
        Number: {invoice.invoice_number}
        Amount: {invoice.amount} {invoice.currency}
        Due Date: {invoice.due_date}
        """
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.client_email]
        )
        email.send()
        
        return Response({'status': 'success'})

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        invoice = self.get_object()
        # Add PDF generation logic here
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        return response
