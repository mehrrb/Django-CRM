from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from users.factories import UserFactory
from django.test import override_settings
import logging
from rest_framework_simplejwt.tokens import RefreshToken
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile

from common.models import Profile, Org, Document, APISettings
from common.factories import (
    OrgFactory, 
    ProfileFactory, 
    DocumentFactory,
    APISettingsFactory
)

logger = logging.getLogger(__name__)
User = get_user_model()

TEST_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'common.middleware.OrgMiddleware',
]

@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class BaseTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.org = OrgFactory()
        self.profile = ProfileFactory(
            user=self.user,
            org=self.org,
            role='ADMIN'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Setup client with auth headers
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
            HTTP_X_ORG=str(self.org.id)
        )

class APISettingsTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.api_settings = APISettingsFactory(
            org=self.org,
            created_by=self.profile
        )
        
    def test_api_settings_crud_operations(self):
        """Test API Settings CRUD operations"""
        url = reverse('common:api-settings-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = {
            "title": "Test API Settings",
            "website": "https://api.test.com"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class DocumentTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.document = DocumentFactory(
            org=self.org,
            created_by=self.profile
        )
        
    def test_document_crud_operations(self):
        """Test document CRUD operations"""
        url = reverse('common:document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class OrgTests(BaseTest):
    def test_org_crud_operations(self):
        """Test organization CRUD operations"""
        url = reverse('common:org-list')
        data = {
            'name': 'Test Org',
            'address': 'Test Address',
            'country': 'US'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class AuthenticationTests(BaseTest):
    def test_invalid_org(self):
        """Test access with invalid org"""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
            HTTP_X_ORG='invalid-org-id'
        )
        url = reverse('common:document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        self.client.credentials()
        url = reverse('common:document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)