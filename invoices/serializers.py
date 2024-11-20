from rest_framework import serializers
from .models import Invoice, InvoiceHistory

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_title',
            'invoice_number',
            'currency',
            'email',
            'due_date',
            'amount',
            'total_amount',
            'status',
            'created_by',
            'created_at',
            'modified_at',
            'from_address',
            'to_address',
            'accounts',
            'assigned_to',
            'teams'
        ]
        read_only_fields = ['created_by', 'created_at', 'modified_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class InvoiceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceHistory
        fields = [
            'id',
            'invoice',
            'status',
            'user',
            'created_at'
        ]
