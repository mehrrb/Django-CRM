from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import override_settings
import jwt
import logging
import os

from contacts.models import Contact
from common.models import Profile, Org, Address
from teams.models import Teams
from users.models import Users
from contacts.serializers import AttachmentSerializer

logger = logging.getLogger(__name__)

@override_settings(MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'contacts.middleware.ProfileMiddleware',  # Use the new middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
])
class ContactTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create user
        self.user = Users.objects.create_user(
            username="testuser",
            email="test@example.com", 
            password="testpass123",
            is_active=True,
            has_sales_access=True,
            has_marketing_access=True
        )
        
        # Create organization
        self.org = Org.objects.create(
            name="Test Organization",
            address="Test Address",
            user=self.user,
            country="US"
        )
        
        # Create profile
        self.profile = Profile.objects.create(
            user=self.user,
            role="ADMIN",
            org=self.org,
            is_active=True,
            has_sales_access=True,
            has_marketing_access=True
        )

        # Create JWT token
        payload = {
            'user_id': str(self.user.id),
            'exp': 1732187943,
            'iat': 1732101543
        }
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        # Set up client authentication
        self.client.force_authenticate(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token}',
            HTTP_ORG=str(self.org.id)
        )

        # Create test data
        self.address = Address.objects.create(
            street="Test Street",
            city="Test City",
            state="Test State",
            postcode="12345",
            country="US"
        )

        # Create contact with user instead of profile
        self.contact = Contact.objects.create(
            first_name="Test",
            last_name="Contact",
            primary_email="test@contact.com",
            mobile_number="+1234567890",
            address=self.address,
            created_by=self.user,  # Using user instead of profile
            org=self.org
        )

        # Assign profile to contact
        self.contact.assigned_to.add(self.profile)

        # Create team with user instead of profile
        self.team = Teams.objects.create(
            name="Test Team",
            created_by=self.user,  # Changed from self.profile to self.user
            org=self.org
        )

        # Set up URLs
        self.list_url = reverse('api_contacts:contact-list')
        self.detail_url = reverse('api_contacts:contact-detail', args=[self.contact.id])
        self.comment_url = reverse('api_contacts:contact-add-comment', args=[self.contact.id])
        self.attachment_url = reverse('api_contacts:contact-attachments', args=[self.contact.id])

        logger.info("Test setup completed successfully")

    def _get_response(self, method, url, data=None, format='json'):
        """Helper method to get response from API"""
        kwargs = {'format': format}
        if data:
            kwargs['data'] = data
            
        if method == 'POST':
            response = self.client.post(url, **kwargs)
        elif method == 'PUT':
            response = self.client.put(url, **kwargs)
        elif method == 'DELETE':
            response = self.client.delete(url)
        else:
            response = self.client.get(url)
            
        return response

    def test_middleware_adds_profile(self):
        """Test that middleware correctly adds profile to request"""
        response = self._get_response('GET', self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(hasattr(response.wsgi_request, 'profile'))
        self.assertEqual(response.wsgi_request.profile.id, self.profile.id)
        logger.info(f"Profile successfully added to request: {response.wsgi_request.profile}")

    def test_contact_list(self):
        response = self._get_response('GET', self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contact_create(self):
        """Test creating a new contact"""
        data = {
            'first_name': 'New',
            'last_name': 'Contact',
            'primary_email': 'new@contact.com',
            'mobile_number': '+989198765432',  # Valid Iranian format
            'status': 'active',
            'source': 'website',
            'company_name': 'New Company'
        }
        response = self._get_response('POST', self.list_url, data)
        print(response.content)  # For debugging
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contact_detail(self):
        response = self._get_response('GET', self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contact_update(self):
        """Test updating a contact"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Contact',
            'primary_email': 'updated@contact.com',
            'mobile_number': '+989198765432',  # Valid Iranian format
            'status': 'active',
            'source': 'website',
            'company_name': 'Updated Company'
        }
        response = self._get_response('PUT', self.detail_url, data)
        print(response.content)  # For debugging
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.first_name, 'Updated')

    def test_contact_delete(self):
        """Test deleting a contact"""
        # Make sure user is admin
        self.profile.role = "ADMIN"
        self.profile.save()
        
        response = self._get_response('DELETE', self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Contact.objects.count(), 0)

    def test_contact_add_comment(self):
        data = {"comment": "Test Comment"}
        response = self._get_response('POST', self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contact_add_attachment(self):
        """Test adding attachment to contact"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create test file
        file_content = b'test content'
        file = SimpleUploadedFile(
            name='test.txt',
            content=file_content,
            content_type='text/plain'
        )
        
        # Test without attachment
        response = self._get_response('POST', self.attachment_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No attachment provided')
        
        # Test with valid attachment
        data = {'attachment': file}
        response = self._get_response(
            'POST',
            self.attachment_url,
            data=data,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Attachments.objects.filter(contact=self.contact).exists())
        
        # Verify attachment data
        attachment = Attachments.objects.get(contact=self.contact)
        self.assertEqual(attachment.created_by, self.user)
        
        # Clean up
        attachment.attachment.delete()

    def test_contact_filter(self):
        response = self._get_response('GET', f"{self.list_url}?name=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)