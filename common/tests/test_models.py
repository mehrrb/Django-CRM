import pytest
from django.core.exceptions import ValidationError
from common.models import Org, Profile, Document, APISettings
from uuid import UUID

@pytest.mark.django_db
class TestOrgModel:
    def test_org_creation(self, org):
        """Test basic organization creation"""
        assert isinstance(org.id, UUID)
        assert org.api_key is not None
        assert len(org.api_key) > 0

    def test_org_str_representation(self, org):
        """Test string representation of organization"""
        assert str(org) == org.name

    def test_get_active_profiles(self, org, profile):
        """Test getting active profiles for an organization"""
        profile.is_active = True
        profile.save()
        active_profiles = org.profiles.filter(is_active=True)
        assert profile in active_profiles

    def test_generate_api_key(self, org):
        """Test API key generation"""
        old_key = org.api_key
        new_key = org.generate_api_key()
        assert len(new_key) > 0
        assert old_key != new_key

@pytest.mark.django_db
class TestProfileModel:
    def test_profile_creation(self, profile):
        """Test basic profile creation"""
        assert isinstance(profile.id, UUID)
        assert profile.user is not None
        assert profile.org is not None

    def test_profile_str_representation(self, profile):
        """Test string representation of profile"""
        expected = f"{profile.user.email} <{profile.org.name}>"
        assert str(profile) == expected

    def test_is_admin_property(self, profile, admin_profile):
        """Test is_admin property"""
        assert not profile.is_admin
        assert admin_profile.is_admin

    def test_user_details_property(self, profile):
        """Test user_details property"""
        details = profile.user_details
        assert details['email'] == profile.user.email
        assert details['id'] == profile.user.id
        assert details['is_active'] == profile.user.is_active

@pytest.mark.django_db
class TestDocumentModel:
    def test_document_creation(self, document):
        assert document.id is not None
        assert document.created_by is not None
        assert document.org is not None
        assert document.created_at is not None

    def test_document_file_type_detection(self, document):
        """Test document file type detection"""
        document.document_file.name = "test.pdf"
        file_type, icon = document.file_type()
        assert file_type == "pdf"
        assert "fa-file-pdf" in icon

        document.document_file.name = "test.jpg"
        file_type, icon = document.file_type()
        assert file_type == "image"
        assert "fa-file-image" in icon

@pytest.mark.django_db
class TestAPISettingsModel:
    def test_api_settings_creation(self, api_settings):
        """Test basic API settings creation"""
        assert api_settings.pk is not None
        assert api_settings.created_by is not None
        assert api_settings.org is not None

    def test_api_settings_str_representation(self, api_settings):
        """Test string representation of API settings"""
        assert str(api_settings) == api_settings.title

    def test_apikey_generation(self, api_settings):
        """Test API key is generated on creation"""
        assert api_settings.apikey is not None
        assert len(api_settings.apikey) > 0