from django.db import models
from django.conf import settings
from common.models import BaseModel

class Invoice(BaseModel):
    CURRENCY_CHOICES = (
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'), 
        ('IRR', 'Iranian Rial'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_title = models.CharField(max_length=200, default="Untitled Invoice")
    email = models.EmailField(default="noreply@example.com")
    
    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    billing_address = models.TextField()
    
    from_address = models.ForeignKey(
        'common.Address',
        related_name='from_invoices',
        on_delete=models.SET_NULL,
        null=True
    )
    to_address = models.ForeignKey(
        'common.Address',
        related_name='to_invoices',
        on_delete=models.SET_NULL,
        null=True
    )
    accounts = models.ManyToManyField('accounts.Account', related_name='invoices')
    assigned_to = models.ManyToManyField('users.Users', related_name='assigned_invoices')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Total Amount"
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.invoice_title}"

class InvoiceComment(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Comment on {self.invoice.invoice_number} by {self.user.username}"

class InvoiceHistory(BaseModel):
    """Model definition for InvoiceHistory."""
    invoice = models.ForeignKey(
        Invoice,
        related_name='invoice_history',
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=20)
    
    class Meta:
        verbose_name = 'Invoice History'
        verbose_name_plural = 'Invoice History'
