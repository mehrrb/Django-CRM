from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from common.tests import ObjectsCreation
from emails.models import Email
from invoices.models import Invoice
from emails.forms import EmailForm

class EmailTest(ObjectsCreation):
    def setUp(self):
        super().setUp()
        self.email = Email.objects.create(
            message_subject="Test Subject",
            message_body="Test Body",
            from_email="test@example.com",
            created_by=self.user,
            org=self.org
        )
        self.invoice = Invoice.objects.create(
            invoice_title="Invoice title",
            invoice_number="INV-001",
            email="test@example.com",
            client_name="Test Client",
            client_email="client@test.com",
            billing_address="Test Address",
            amount=100,
            currency="USD",
            due_date="2024-01-01",
            user=self.user
        )
        # URLs
        self.list_url = reverse('api_emails:email-list')
        self.detail_url = reverse('api_emails:email-detail', args=[self.email.id])
        self.compose_url = reverse('api_emails:email-compose')
        self.sent_url = reverse('api_emails:email-sent')
        self.draft_url = reverse('api_emails:email-draft')
        self.trash_url = reverse('api_emails:email-trash')
        self.important_url = reverse('api_emails:email-important')

    def test_email_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_create(self):
        data = {
            "message_subject": "New Email",
            "message_body": "New Body",
            "from_email": "new@test.com",
            "to_email": "to@test.com"
        }
        response = self.client.post(self.compose_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_email_create_invalid(self):
        data = {
            "message_subject": "New Email",
            "message_body": "New Body",
            "from_email": "new@test.com",
            "to_email": ""  # Invalid - required field
        }
        response = self.client.post(self.compose_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message_subject'], "Test Subject")

    def test_email_update(self):
        data = {
            "message_subject": "Updated Subject",
            "message_body": "Updated Body",
            "from_email": "updated@test.com",
            "to_email": "to@test.com"
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message_subject'], "Updated Subject")

    def test_email_delete(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_email_sent_list(self):
        response = self.client.get(self.sent_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_draft_list(self):
        response = self.client.get(self.draft_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_trash_list(self):
        response = self.client.get(self.trash_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_important_list(self):
        response = self.client.get(self.important_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_move_to_trash(self):
        url = reverse('api_emails:email-move-to-trash', args=[self.email.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Email.objects.get(id=self.email.id).is_trash)

    def test_email_mark_important(self):
        url = reverse('api_emails:email-mark-important', args=[self.email.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Email.objects.get(id=self.email.id).important)

    def test_form_validation(self):
        # Valid form
        form_data = {
            "from_email": "john@doe.com",
            "to_email": "jane@doe.com",
            "subject": "test subject",
            "message": "test message",
        }
        form = EmailForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Invalid form
        invalid_form_data = {
            "from_email": "john@doe.com",
            "to_email": "",  # Required field
            "subject": "test subject",
            "message": "test message",
        }
        form = EmailForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

    def test_email_draft_operations(self):
        # Create draft
        data = {
            "message_subject": "Draft Email",
            "message_body": "Draft Body",
            "from_email": "draft@test.com",
            "to_email": "to@test.com",
            "is_draft": True
        }
        response = self.client.post(self.compose_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get draft
        draft_id = response.data['id']
        url = reverse('api_emails:email-detail', args=[draft_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_draft'])

        # Delete draft
        url = reverse('api_emails:email-draft-delete', args=[draft_id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)