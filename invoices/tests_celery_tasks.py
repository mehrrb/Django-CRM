from rest_framework.test import APITestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import Users
from teams.models import Teams
from accounts.models import Account
from invoices.models import Invoice, InvoiceHistory
from common.models import Comment, Attachments
from invoices.tasks import (
    send_email, 
    send_invoice_email, 
    send_invoice_email_cancel,
    send_invoice_status_email,
    send_invoice_deleted_email
)

class InvoiceCeleryTaskTest(APITestCase):
    def setUp(self):
        # Create users
        self.user = Users.objects.create_user(
            email="test@example.com",
            password="password",
            is_active=True
        )
        self.user1 = Users.objects.create_user(
            email="test1@example.com",
            password="password",
            is_active=True
        )
        
        # Create team
        self.team = Teams.objects.create(name="Test Team")
        self.team.users.add(self.user, self.user1)
        
        # Create account
        self.account = Account.objects.create(
            name="Test Account",
            email="account@example.com",
            created_by=self.user
        )
        
        # Create invoice
        self.invoice = Invoice.objects.create(
            invoice_title="Test Invoice",
            invoice_number="INV-001",
            currency="USD",
            email="test@invoice.com",
            due_date="2024-12-31",
            amount=1000.00,
            total_amount=1000.00,
            status="draft",
            user=self.user
        )
        
        # Create invoice history
        self.history = InvoiceHistory.objects.create(
            invoice=self.invoice,
            status="draft",
            user=self.user
        )
        
        # Create attachment
        self.attachment = Attachments.objects.create(
            attachment=SimpleUploadedFile("test.txt", b"test content"),
            created_by=self.user,
            invoice=self.invoice
        )
        
        self.client.force_authenticate(user=self.user)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_email_task(self):
        task = send_email.apply((
            self.invoice.id,
            [self.user.id, self.user1.id]
        ))
        self.assertEqual("SUCCESS", task.state)
        
        # Test with invalid user IDs
        task = send_email.apply((
            self.invoice.id,
            [99999]
        ))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_invoice_email_task(self):
        task = send_invoice_email.apply((self.invoice.id,))
        self.assertEqual("SUCCESS", task.state)
        
        # Test with invalid invoice ID
        task = send_invoice_email.apply((99999,))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_invoice_cancel_email_task(self):
        task = send_invoice_email_cancel.apply((self.invoice.id,))
        self.assertEqual("SUCCESS", task.state)
        
        # Test with invalid invoice ID
        task = send_invoice_email_cancel.apply((99999,))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_invoice_status_email_task(self):
        task = send_invoice_status_email.apply((
            self.invoice.id,
            "paid",
            [self.user.id]
        ))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_invoice_deleted_email_task(self):
        task = send_invoice_deleted_email.apply((
            self.invoice.id,
            [self.user.id]
        ))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_task_chaining(self):
        # Test chaining multiple tasks
        task = (
            send_invoice_email.s(self.invoice.id) |
            send_email.s([self.user.id, self.user1.id])
        ).apply_async()
        self.assertEqual("SUCCESS", task.state)

    def test_task_error_handling(self):
        with self.assertRaises(Invoice.DoesNotExist):
            send_invoice_email.apply((99999,))

        with self.assertRaises(Users.DoesNotExist):
            send_email.apply((self.invoice.id, [99999]))

    def test_task_with_attachments(self):
        task = send_invoice_email.apply((self.invoice.id,))
        self.assertEqual("SUCCESS", task.state)
        self.assertTrue(self.attachment in self.invoice.attachments.all())

    def test_task_with_history(self):
        task = send_invoice_status_email.apply((
            self.invoice.id,
            "paid",
            [self.user.id]
        ))
        self.assertEqual("SUCCESS", task.state)
        self.assertTrue(InvoiceHistory.objects.filter(
            invoice=self.invoice,
            status="paid"
        ).exists())