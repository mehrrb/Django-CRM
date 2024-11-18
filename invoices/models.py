from django.db import models
from django.conf import settings
from common.models import BaseModel

class Invoice(BaseModel):
    CURRENCY_CHOICES = (
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('INR', 'Indian Rupee'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    billing_address = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.client_name}"

class InvoiceComment(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Comment on {self.invoice.invoice_number} by {self.user.username}"
