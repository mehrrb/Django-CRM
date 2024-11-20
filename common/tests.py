from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from common.models import (
    Org, 
    Address, 
    Comment, 
    Attachments,
    Document
)
from teams.models import Teams

User = get_user_model()

class ObjectsCreation(APITestCase):
    def setUp(self):
        # Create main user
        self.user = User.objects.create_user(
            email="user@example.com",
            username="testuser",
            password="password",
            has_sales_access=True,
            has_marketing_access=True,
            is_active=True
        )
        
        # Create additional users
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            username="testuser2",
            password="password",
            is_active=True
        )
        
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="password",
            is_active=True
        )
        
        # Create organization
        self.org = Org.objects.create(
            name="Test Organization",
            address="Test Address",
            user=self.user,
            country="US",
            is_active=True
        )
        
        # Add users to org
        self.user.org = self.org
        self.user.save()
        self.user2.org = self.org
        self.user2.save()
        
        # Create team
        self.team = Teams.objects.create(
            name="Test Team",
            created_by=self.user,
            org=self.org
        )
        self.team.users.add(self.user, self.user2)
        
        # Create address
        self.address = Address.objects.create(
            street="123 Test St",
            city="Test City",
            state="Test State",
            postcode="12345",
            country="US",
            org=self.org
        )
        
        # Create comment
        self.comment = Comment.objects.create(
            comment="Test Comment",
            user=self.user,
            org=self.org
        )
        
        # Create attachment
        self.attachment = Attachments.objects.create(
            attachment=SimpleUploadedFile("test.txt", b"test content"),
            created_by=self.user,
            org=self.org
        )
        
        # Create document
        self.document = Document.objects.create(
            title="Test Document",
            document=SimpleUploadedFile("test.doc", b"test content"),
            created_by=self.user,
            org=self.org
        )
        
        # URLs
        self.org_list_url = reverse('api_common:org-list')
        self.org_detail_url = reverse('api_common:org-detail', args=[self.org.id])
        self.user_list_url = reverse('api_common:user-list')
        self.user_detail_url = reverse('api_common:user-detail', args=[self.user.id])
        self.comment_list_url = reverse('api_common:comment-list')
        self.attachment_list_url = reverse('api_common:attachment-list')
        self.document_list_url = reverse('api_common:document-list')
        
        # Authenticate the user
        self.client.force_authenticate(user=self.user)

    def create_user(self, email, **kwargs):
        """Helper method to create users"""
        return User.objects.create_user(
            email=email,
            username=email.split('@')[0],
            password="password",
            is_active=True,
            org=self.org,
            **kwargs
        )

    def test_org_list(self):
        response = self.client.get(self.org_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_org_detail(self):
        response = self.client.get(self.org_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Organization")

    def test_user_list(self):
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_detail(self):
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "user@example.com")

    def test_comment_create(self):
        data = {
            'comment': 'New Comment',
            'user': self.user.id
        }
        response = self.client.post(self.comment_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_attachment_create(self):
        data = {
            'attachment': SimpleUploadedFile("new.txt", b"new content"),
            'created_by': self.user.id
        }
        response = self.client.post(self.attachment_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_document_create(self):
        data = {
            'title': 'New Document',
            'document': SimpleUploadedFile("new.doc", b"new content"),
            'created_by': self.user.id
        }
        response = self.client.post(self.document_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_permissions(self):
        # Test unauthorized access
        self.client.logout()
        response = self.client.get(self.org_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test different org user
        different_org_user = self.create_user("other@test.com")
        self.client.force_authenticate(user=different_org_user)
        response = self.client.get(self.org_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)