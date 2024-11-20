from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from common.tests import ObjectsCreation
from contacts.models import Contact
from teams.models import Teams

class ContactTest(ObjectsCreation):
    def setUp(self):
        super().setUp()
        self.contact = Contact.objects.create(
            first_name="Test",
            last_name="Contact",
            email="test@contact.com",
            phone="1234567890",
            address=self.address,
            description="Test Contact Description",
            created_by=self.user,
            org=self.org
        )
        
        self.team = Teams.objects.create(
            name="Test Team",
            created_by=self.user,
            org=self.org
        )
        
        # URLs
        self.list_url = reverse('api_contacts:contact-list')
        self.detail_url = reverse('api_contacts:contact-detail', args=[self.contact.id])
        self.comment_url = reverse('api_contacts:contact-add-comment', args=[self.contact.id])
        self.attachment_url = reverse('api_contacts:contact-add-attachment', args=[self.contact.id])
        self.bulk_url = reverse('api_contacts:contact-bulk-action')

    def test_contact_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contact_create(self):
        data = {
            "first_name": "New",
            "last_name": "Contact",
            "email": "new@contact.com",
            "phone": "9876543210",
            "address": self.address.id,
            "teams": [self.team.id],
            "assigned_to": [self.user.id]
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), 2)

    def test_contact_create_invalid(self):
        data = {
            "first_name": "",  # Required field
            "last_name": "Contact",
            "email": "invalid-email"  # Invalid email
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_contact_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], "Test")
        self.assertEqual(response.data['email'], "test@contact.com")

    def test_contact_update(self):
        data = {
            "first_name": "Updated",
            "last_name": "Contact",
            "email": "updated@contact.com"
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], "Updated")

    def test_contact_delete(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Contact.objects.count(), 0)

    def test_contact_add_comment(self):
        data = {
            "comment": "Test Comment"
        }
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contact_add_attachment(self):
        data = {
            "attachment": "test.txt",
            "title": "Test Attachment"
        }
        response = self.client.post(self.attachment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contact_bulk_action(self):
        data = {
            "contact_ids": [self.contact.id],
            "action": "delete"
        }
        response = self.client.post(self.bulk_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contact_filter(self):
        # Test name filter
        response = self.client.get(f"{self.list_url}?name=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test email filter
        response = self.client.get(f"{self.list_url}?email=test@contact.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_contact_permissions(self):
        # Test unauthorized access
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with different org user
        different_org_user = self.create_user("other@test.com")
        self.client.force_authenticate(user=different_org_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)