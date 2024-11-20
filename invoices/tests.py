from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from users.models import Users
from teams.models import Teams
from accounts.models import Account
from common.models import Comment, Attachments
from .models import Invoice, InvoiceHistory
from .tasks import send_email, send_invoice_email, send_invoice_email_cancel

class InvoiceBaseTest(APITestCase):
    def setUp(self):
        # Create users
        self.user = Users.objects.create_user(
            email="johnDoeInvoice@example.com", 
            password="password"
        )
        self.user1 = Users.objects.create_user(
            email="janeDoeInvoice@example.com", 
            password="password"
        )
        self.user2 = Users.objects.create_user(
            email="joeInvoice@example.com", 
            password="password"
        )

        # Create team
        self.team_dev = Teams.objects.create(name="Dev Team")
        self.team_dev.users.add(self.user, self.user1)

        # Create account
        self.account = Account.objects.create(
            name="Test Account",
            email="account@example.com",
            created_by=self.user
        )

        # Create invoice
        self.invoice = Invoice.objects.create(
            invoice_title="Test Invoice",
            invoice_number="invoice number",
            currency="USD",
            email="invoiceTitle@email.com",
            due_date="2024-11-22",
            amount=1000.00,
            total_amount=1000.00,
            status="draft",
            user=self.user
        )

        # Create invoice history
        self.invoice_history = InvoiceHistory.objects.create(
            invoice=self.invoice,
            status="draft",
            user=self.user
        )

        # Create comment
        self.comment = Comment.objects.create(
            comment="Test Comment",
            user=self.user,
            invoice=self.invoice
        )

        # Create attachment
        self.attachment = Attachments.objects.create(
            attachment=SimpleUploadedFile("test.txt", b"test content"),
            created_by=self.user,
            invoice=self.invoice
        )

        # URLs
        self.list_url = reverse('api_invoices:invoice-list')
        self.detail_url = reverse('api_invoices:invoice-detail', args=[self.invoice.id])
        self.email_url = reverse('api_invoices:invoice-send-email', args=[self.invoice.id])
        self.cancel_url = reverse('api_invoices:invoice-cancel', args=[self.invoice.id])
        self.status_url = reverse('api_invoices:invoice-change-status', args=[self.invoice.id])
        self.comment_url = reverse('api_invoices:invoice-add-comment')
        self.attachment_url = reverse('api_invoices:invoice-add-attachment')

class InvoiceListTest(InvoiceBaseTest):
    def test_get_invoice_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_invoice(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'invoice_title': "invoice title",
            'status': "Draft",
            'invoice_number': "INV123",
            'currency': "INR",
            'email': "invoice@example.com",
            'due_date': (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            'total_amount': "1234",
            'teams': [self.team_dev.id],
            'accounts': [self.account.id],
            'assigned_to': [self.user1.id],
            'quantity': 0
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invoice_filter(self):
        self.client.force_authenticate(user=self.user)
        # Test invoice number filter
        response = self.client.get(f"{self.list_url}?invoice_number=invoice number")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test status filter
        response = self.client.get(f"{self.list_url}?status=draft")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class InvoiceDetailTest(InvoiceBaseTest):
    def test_get_invoice_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_invoice(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "invoice_title": "Updated Invoice",
            "amount": 1500.00
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['invoice_title'], "Updated Invoice")

    def test_delete_invoice(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class InvoiceActionTest(InvoiceBaseTest):
    def test_send_email(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "recipient_emails": ["client@test.com"],
            "subject": "Test Invoice Email",
            "message": "Please find attached invoice"
        }
        response = self.client.post(self.email_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancel_invoice(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "cancelled")

    def test_change_status(self):
        self.client.force_authenticate(user=self.user)
        data = {"status": "paid"}
        response = self.client.post(self.status_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "paid")

class InvoiceCommentTest(InvoiceBaseTest):
    def test_add_comment(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'comment': 'test comment invoice',
            'invoice_id': self.invoice.id
        }
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_comment(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'comment': 'updated comment'
        }
        url = reverse('api_invoices:invoice-update-comment', args=[self.comment.id])
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class InvoiceAttachmentTest(InvoiceBaseTest):
    def test_add_attachment(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'attachment': SimpleUploadedFile("file.txt", b"file content"),
            'invoice_id': self.invoice.id
        }
        response = self.client.post(self.attachment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_delete_attachment(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api_invoices:invoice-remove-attachment', args=[self.attachment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

class InvoiceCeleryTest(InvoiceBaseTest):
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_invoice_email_tasks(self):
        # Test send email task
        task = send_email.apply((self.invoice.id, [self.user.id]))
        self.assertEqual("SUCCESS", task.state)

        # Test send invoice email task
        task = send_invoice_email.apply((self.invoice.id,))
        self.assertEqual("SUCCESS", task.state)

        # Test send invoice cancel email task
        task = send_invoice_email_cancel.apply((self.invoice.id,))
        self.assertEqual("SUCCESS", task.state)