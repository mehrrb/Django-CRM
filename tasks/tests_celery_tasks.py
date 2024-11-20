from django.test import TestCase
from django.test.utils import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from tasks.celery_tasks import (
    send_email,
    send_task_assigned_email,
    send_task_status_email,
    send_task_deleted_email,
    send_task_comment_email
)
from tasks.tests import TaskCreateTest
from common.models import User, Comment, Attachments

class TestTaskCeleryTasks(TaskCreateTest, TestCase):
    def setUp(self):
        super().setUp()
        
        # Create additional users
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="test123",
            is_active=True,
            org=self.org
        )
        
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="test123",
            is_active=True,
            org=self.org
        )
        
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

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_send_task_email(self):
        task = send_email.apply(
            (
                self.task.id,
                [self.user.id, self.user1.id],
            )
        )
        self.assertEqual("SUCCESS", task.state)
        
        # Test with invalid task ID
        task = send_email.apply((99999, [self.user.id]))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_send_task_assigned_email(self):
        task = send_task_assigned_email.apply(
            (
                self.task.id,
                [self.user.id, self.user1.id],
                "assigned"
            )
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_send_task_status_email(self):
        task = send_task_status_email.apply(
            (
                self.task.id,
                "completed",
                [self.user.id]
            )
        )
        self.assertEqual("SUCCESS", task.state)
        
        # Test different statuses
        statuses = ["New", "In Progress", "Completed", "Canceled"]
        for status in statuses:
            task = send_task_status_email.apply(
                (self.task.id, status, [self.user.id])
            )
            self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_send_task_deleted_email(self):
        task = send_task_deleted_email.apply(
            (
                self.task.id,
                [self.user.id]
            )
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_send_task_comment_email(self):
        task = send_task_comment_email.apply(
            (
                self.comment.id,
                [self.user.id]
            )
        )
        self.assertEqual("SUCCESS", task.state)

    def test_task_error_handling(self):
        # Test with invalid task ID
        task = send_email.apply((99999, [self.user.id]))
        self.assertEqual("SUCCESS", task.state)

        # Test with invalid user IDs
        task = send_email.apply((self.task.id, [99999]))
        self.assertEqual("SUCCESS", task.state)

    def test_task_with_attachments(self):
        task = send_email.apply(
            (
                self.task.id,
                [self.user.id],
            )
        )
        self.assertEqual("SUCCESS", task.state)
        self.assertTrue(self.attachment in self.task.attachments.all())

    def test_task_with_multiple_recipients(self):
        task = send_email.apply(
            (
                self.task.id,
                [self.user.id, self.user1.id, self.user2.id]
            )
        )
        self.assertEqual("SUCCESS", task.state)