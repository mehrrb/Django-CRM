from django.db import models
from common.models import User, Org
from accounts.models import Account

class Report(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=50, choices=[
        ('lead', 'Lead Report'),
        ('account', 'Account Report'),
        ('sales', 'Sales Report')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def generate_report(self):
        if self.report_type == 'lead':
            return Lead.objects.filter(org=self.org).values()
        elif self.report_type == 'account':
            return Account.objects.filter(org=self.org).values() 