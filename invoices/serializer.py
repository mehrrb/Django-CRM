from rest_framework import serializers
from invoices.models import Invoice, InvoiceComment

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'client_name',
            'client_email',
            'billing_address',
            'amount',
            'currency',
            'due_date',
            'status',
            'description',
            'created_by',
            'created_at',
            'modified_at'
        ]

class InvoiceCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceComment
        fields = [
            'id',
            'invoice',
            'comment',
            'user',
            'created_at'
        ]


