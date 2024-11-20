from django.db import models
from django.conf import settings
from common.base import BaseModel
from contacts.models import Contact

class Email(BaseModel):
    from_account = models.ForeignKey(
        'accounts.Account',
        related_name='sent_emails',
        on_delete=models.SET_NULL,
        null=True
    )
    from_email = models.EmailField(default="noreply@example.com")
    recipients = models.ManyToManyField(
        Contact,
        related_name='received_emails'
    )
    message_subject = models.TextField(null=True)
    message_body = models.TextField(null=True)

    is_draft = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    is_trash = models.BooleanField(default=False) 
    is_important = models.BooleanField(default=False)
    user = models.ForeignKey(
        'users.Users',
        on_delete=models.CASCADE,
        related_name='emails',
        null=True
    )

    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        db_table = "emails"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.message_subject}"