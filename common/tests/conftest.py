import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from common.factories import (
    UserFactory, 
    OrgFactory,
    ProfileFactory,
    DocumentFactory,
    APISettingsFactory
)

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return UserFactory.create()

@pytest.fixture
def another_user():
    return UserFactory.create()

@pytest.fixture
def org():
    return OrgFactory.create()

@pytest.fixture
def profile(user, org):
    return ProfileFactory.create(
        user=user,
        org=org,
        is_active=True,
        is_organization_admin=False
    )

@pytest.fixture
def admin_profile(another_user, org):
    return ProfileFactory.create(
        user=another_user,
        org=org,
        is_active=True,
        is_organization_admin=True
    )

@pytest.fixture
def document(profile):
    return DocumentFactory.create(
        created_by=profile,
        org=profile.org,
        document_file=None 
    )

@pytest.fixture
def api_settings(profile):
    return APISettingsFactory.create(
        created_by=profile,
        org=profile.org
    )

@pytest.fixture
def auth_headers(profile):
    """Generate authentication headers for a profile"""
    from rest_framework_simplejwt.tokens import AccessToken
    token = AccessToken.for_user(profile.user)
    return {
        'HTTP_AUTHORIZATION': f'Bearer {token}',
        'HTTP_ORG': str(profile.org.id)
    }