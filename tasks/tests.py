from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from common.tests import ObjectsCreation
from tasks.models import Task
from common.models import Comment, Attachments
from teams.models import Teams

class TaskCreateTest(ObjectsCreation):
    def setUp(self):
        super().setUp()
        
        # Create task
        self.task = Task.objects.create(
            title="Test Task",
            status="New",
            priority="High",
            due_date="2024-12-31",
            description="Test Description",
            created_by=self.user,
            org=self.org
        )
        
        # Add assigned users
        self.task.assigned_to.add(self.user, self.user2)
        
        # Create team
        self.team = Teams.objects.create(
            name="Test Team",
            created_by=self.user,
            org=self.org
        )
        self.team.users.add(self.user, self.user2)
        self.task.teams.add(self.team)
        
        # Create comment
        self.comment = Comment.objects.create(
            comment="Test Comment",
            task=self.task,
            commented_by=self.user,
            org=self.org
        )
        
        # Create attachment
        self.attachment = Attachments.objects.create(
            attachment=SimpleUploadedFile("test.txt", b"test content"),
            task=self.task,
            created_by=self.user,
            org=self.org
        )
        
        # URLs
        self.task_list_url = reverse('api_tasks:task-list')
        self.task_detail_url = reverse('api_tasks:task-detail', args=[self.task.id])
        self.task_comment_url = reverse('api_tasks:task-comments', args=[self.task.id])
        self.task_attachment_url = reverse('api_tasks:task-attachments', args=[self.task.id])
        
        self.client.force_authenticate(user=self.user)

    def test_task_create(self):
        data = {
            "title": "New Task",
            "status": "In Progress",
            "priority": "Medium",
            "due_date": "2024-12-31",
            "description": "New Task Description",
            "assigned_to": [self.user.id]
        }
        response = self.client.post(self.task_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_task_list(self):
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_task_detail(self):
        response = self.client.get(self.task_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Task")

    def test_task_update(self):
        data = {
            "title": "Updated Task",
            "status": "Completed"
        }
        response = self.client.patch(self.task_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Updated Task")

    def test_task_delete(self):
        response = self.client.delete(self.task_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_task_comment(self):
        data = {
            "comment": "New Comment",
            "task": self.task.id,
            "commented_by": self.user.id
        }
        response = self.client.post(self.task_comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_task_attachment(self):
        data = {
            "attachment": SimpleUploadedFile("new.txt", b"new content"),
            "task": self.task.id,
            "created_by": self.user.id
        }
        response = self.client.post(self.task_attachment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_task_filters(self):
        # Test status filter
        response = self.client.get(f"{self.task_list_url}?status=New")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test priority filter
        response = self.client.get(f"{self.task_list_url}?priority=High")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_task_permissions(self):
        # Test unauthorized access
        self.client.logout()
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test different org user
        different_org_user = self.create_user("other@test.com")
        self.client.force_authenticate(user=different_org_user)
        response = self.client.get(self.task_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_validation(self):
        # Test invalid priority
        data = {
            "title": "Invalid Task",
            "priority": "Invalid"
        }
        response = self.client.post(self.task_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test invalid status
        data = {
            "title": "Invalid Task",
            "status": "Invalid"
        }
        response = self.client.post(self.task_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)