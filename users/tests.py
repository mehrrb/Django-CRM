from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import Users

class UserTest(APITestCase):
    def setUp(self):
        self.user = Users.objects.create_user(
            email="test@example.com",
            password="testpass123",
            is_active=True
        )
        self.login_url = reverse('users:login')
        self.register_url = reverse('users:user-list')
        self.me_url = reverse('users:me')

    def test_user_registration(self):
        data = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "confirm_password": "newpass123"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_login(self):
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data['data'])

    def test_get_user_details(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)