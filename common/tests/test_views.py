import pytest
from django.urls import reverse
from rest_framework import status
from common.middleware.get_company import OrgMiddleware

@pytest.mark.django_db
class TestProfileViewSet:
    def setup_method(self):
        """Setup for each test method"""
        self.middleware = OrgMiddleware(lambda x: x)

    def test_list_profiles(self, api_client, profile, auth_headers):
        """Test listing profiles"""
        api_client.force_authenticate(user=profile.user)
        
        # Add JWT token to headers
        from rest_framework_simplejwt.tokens import AccessToken
        token = str(AccessToken.for_user(profile.user))
        auth_headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        auth_headers['HTTP_X_ORG'] = str(profile.org.id)
        
        url = reverse('common:profile-list')
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_create_profile(self, api_client, user, org, auth_headers):
        """Test creating a new profile"""
        url = reverse('common:profile-list')
        data = {
            'user': user.id,
            'org': org.id,
            'role': 'ADMIN'
        }
        response = api_client.post(url, data, format='json', **auth_headers)
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_profile(self, api_client, profile, auth_headers):
        """Test updating a profile"""
        api_client.force_authenticate(user=profile.user)
        request = api_client.get('/').wsgi_request
        request.user = profile.user
        self.middleware.process_request(request)
        
        url = reverse('common:profile-detail', args=[profile.id])
        data = {'role': 'ADMIN'}
        response = api_client.patch(url, data, format='json', **auth_headers)
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestDocumentViewSet:
    def setup_method(self):
        """Setup for each test method"""
        self.middleware = OrgMiddleware(lambda x: x)

    def test_list_documents(self, api_client, document, profile, auth_headers):
        """Test listing documents"""
        api_client.force_authenticate(user=profile.user)
        
        # Add JWT token to headers
        from rest_framework_simplejwt.tokens import AccessToken
        token = str(AccessToken.for_user(profile.user))
        auth_headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        auth_headers['HTTP_X_ORG'] = str(profile.org.id)
        
        url = reverse('common:document-list')
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

    def test_create_document(self, api_client, profile, auth_headers):
        """Test creating a new document"""
        url = reverse('common:document-list')
        data = {
            'title': 'Test Document',
            'status': 'active',
            'org': profile.org.id
        }
        response = api_client.post(url, data, **auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == data['title']

    def test_share_document(self, api_client, document, profile, auth_headers):
        """Test sharing a document"""
        url = reverse('common:document-share', kwargs={'pk': document.pk})
        data = {
            'shared_to': [profile.id],
            'comment': 'Sharing this document'
        }
        response = api_client.post(url, data, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        document.refresh_from_db()
        assert profile in document.shared_to.all()