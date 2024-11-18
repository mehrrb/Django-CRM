from django import forms
from invoices.models import Invoice, InvoiceComment

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'invoice_number',
            'client_name',
            'client_email',
            'billing_address',
            'amount',
            'currency',
            'due_date',
            'status',
            'description'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class InvoiceCommentForm(forms.ModelForm):
    class Meta:
        model = InvoiceComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }
