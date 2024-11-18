from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import User, Org
from accounts.models import Account


class Report(models.Model):
    """
    Model for storing and managing different types of reports in the system
    """

    class ReportTypes(models.TextChoices):
        ACCOUNT = 'account', _('Account Report') 
        SALES = 'sales', _('Sales Report')

    name = models.CharField(
        max_length=200,
        verbose_name=_('Name')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Created By')
    )
    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Organization')
    )
    report_type = models.CharField(
        max_length=50,
        choices=ReportTypes.choices,
        verbose_name=_('Report Type')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['org', 'report_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"

    def generate_report(self):
        """Generate report based on report type"""
        report_generators = {
            self.ReportTypes.ACCOUNT: self._generate_account_report,
            self.ReportTypes.SALES: self._generate_sales_report,
        }
        
        generator = report_generators.get(self.report_type)
        if not generator:
            raise ValueError(f"Invalid report type: {self.report_type}")
            
        return generator()

    def _generate_account_report(self):
        """Generate account report"""
        return Account.objects.filter(org=self.org).select_related(
            'created_by',
            'assigned_to'
        ).values(
            'id',
            'name',
            'website',
            'phone',
            'created_by__email',
            'created_at'
        )

    def _generate_sales_report(self):
        """Generate sales report"""
        # TODO: Implement sales report generation
        raise NotImplementedError("Sales report generation not implemented yet")
    