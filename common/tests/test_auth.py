import pytest
from rest_framework import status
from django.urls import reverse
from common.external_auth import verify_jwt_token
from common.permissions import IsOrgAdmin, IsOrgMember
from common.factories import APISettingsFactory
from common.token_generator import generate_key

@pytest.mark.django_db
class TestAuthentication:
    def test_jwt_token_verification(self, profile):
        """Test JWT token verification"""
        from rest_framework_simplejwt.tokens import AccessToken
        token = str(AccessToken.for_user(profile.user))
        is_valid, payload = verify_jwt_token(token)
        assert is_valid
        assert str(payload['user_id']) == str(profile.user.id)

    def test_api_key_auth(self, api_client, org, profile):
        """Test API key authentication"""
        api_key = generate_key()
        
        api_settings = APISettingsFactory(
            org=org,
            created_by=profile,
            api_key=api_key  # Use api_key instead of token
        )
        
        headers = {
            'HTTP_API_KEY': api_settings.api_key,
            'HTTP_ORG': str(org.id)
        }
        
        url = reverse('common:document-list')
        response = api_client.get(url, **headers)
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_token(self, api_client):
        """Test invalid token"""
        headers = {
            'HTTP_TOKEN': 'invalid_token',
            'HTTP_ORG': 'invalid_org'
        }
        url = reverse('common:document-list')
        response = api_client.get(url, **headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestPermissions:
    def test_org_admin_permission(self, admin_profile):
        """Test organization admin permissions"""
        permission = IsOrgAdmin()
        request = type('Request', (), {'profile': admin_profile})()
        assert permission.has_permission(request, None)

    def test_org_member_permission(self, profile):
        """Test organization member permissions"""
        permission = IsOrgMember()
        request = type('Request', (), {'profile': profile})()
        assert permission.has_permission(request, None)

    def test_non_member_permission(self, profile):
        """Test permissions for non-members"""
        profile.org = None
        permission = IsOrgMember()
        request = type('Request', (), {'profile': profile})()
        assert not permission.has_permission(request, None)