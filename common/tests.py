from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from django.test import override_settings
from django.contrib.auth.models import Group
from django.conf import settings
import jwt
import logging

from common.models import (
    Profile,
    Org,
    Document,
    Comment,
    APISettings
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
    'common.middleware.get_company.GetProfileAndOrg',
]

@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class BaseTest(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_active=True
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
            has_marketing_access=True,
            is_organization_admin=True
        )

        # Create JWT token
        payload = {
            'user_id': str(self.user.id),
            'exp': 1732187943,
            'iat': 1732101543,
            'jti': 'test-jwt-id',
            'token_type': 'access'
        }
        
        # Get JWT settings from Django settings
        jwt_algo = getattr(settings, 'JWT_ALGO', 'HS256')
        
        self.token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=jwt_algo
        )

        # Login the user
        self.client.login(username="testuser", password="testpass123")
        
        # Set up client credentials
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token}',
            HTTP_ORG=str(self.org.id)
        )

        logger.info(f"Test Setup Complete:")
        logger.info(f"User ID: {self.user.id}")
        logger.info(f"Org ID: {self.org.id}")
        logger.info(f"Profile ID: {self.profile.id}")
        logger.info(f"Token: {self.token}")

class CommonViewSetTests(BaseTest):
    def test_org_get(self):
        url = reverse('api_common:common-org')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_org_create(self):
        url = reverse('api_common:common-org')
        data = {
            "name": "NewOrganization"  # No special characters, just name field
        }
        
        logger.info(f"POST Request:")
        logger.info(f"URL: {url}")
        logger.info(f"Data: {data}")
        
        response = self.client.post(url, data, format='json')
        
        # Log the response content to see validation errors
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Content: {response.content.decode()}")
        
        if response.status_code != status.HTTP_201_CREATED:
            logger.error(f"Validation errors: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)