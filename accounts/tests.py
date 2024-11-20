from rest_framework.test import APITestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import Users
from teams.models import Teams
from accounts.models import Account, Tags, Email
from common.models import Comment, Attachments
from accounts.tasks import (
    send_email_to_assigned_user,
    send_account_status_email,
    send_account_deleted_email,
    send_account_email
)

class AccountCeleryTaskTest(APITestCase):
    def setUp(self):
        # Create users
        self.user = Users.objects.create_user(
            email="test@example.com",
            password="password",
            is_active=True
        )
        self.user1 = Users.objects.create_user(
            email="test1@example.com",
            password="password",
            is_active=True
        )
        
        # Create team
        self.team = Teams.objects.create(name="Test Team")
        self.team.users.add(self.user, self.user1)
        
        # Create account
        self.account = Account.objects.create(
            name="Test Account",
            email="account@example.com",
            created_by=self.user
        )
        
        # Create tags
        self.tag = Tags.objects.create(name="Test Tag")
        self.account.tags.add(self.tag)
        
        # Create email
        self.email = Email.objects.create(
            subject="Test Email",
            message_body="Test Body",
            from_account=self.account,
            created_by=self.user
        )
        
        # Create attachment
        self.attachment = Attachments.objects.create(
            attachment=SimpleUploadedFile("test.txt", b"test content"),
            created_by=self.user,
            account=self.account
        )
        
        self.client.force_authenticate(user=self.user)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_email_to_assigned_user_task(self):
        task = send_email_to_assigned_user.apply((
            [self.user.id, self.user1.id],
            self.account.id,
            "assigned"
        ))
        self.assertEqual("SUCCESS", task.state)
        
        # Test with invalid user IDs
        task = send_email_to_assigned_user.apply((
            [99999],
            self.account.id,
            "assigned"
        ))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_account_status_email_task(self):
        task = send_account_status_email.apply((
            self.account.id,
            "active",
            [self.user.id]
        ))
        self.assertEqual("SUCCESS", task.state)
        
        # Test with invalid account ID
        task = send_account_status_email.apply((
            99999,
            "active",
            [self.user.id]
        ))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_account_deleted_email_task(self):
        task = send_account_deleted_email.apply((
            self.account.id,
            [self.user.id]
        ))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_send_account_email_task(self):
        task = send_account_email.apply((
            self.email.id,
            [self.user.id]
        ))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory"
    )
    def test_task_chaining(self):
        # Test chaining multiple tasks
        task = (
            send_account_status_email.s(self.account.id, "active") |
            send_email_to_assigned_user.s([self.user.id, self.user1.id])
        ).apply_async()
        self.assertEqual("SUCCESS", task.state)

    def test_task_error_handling(self):
        with self.assertRaises(Account.DoesNotExist):
            send_account_status_email.apply((99999, "active", [self.user.id]))

        with self.assertRaises(Users.DoesNotExist):
            send_email_to_assigned_user.apply(([99999], self.account.id, "assigned"))

    def test_task_with_attachments(self):
        task = send_account_email.apply((self.email.id, [self.user.id]))
        self.assertEqual("SUCCESS", task.state)
        self.assertTrue(self.attachment in self.account.attachments.all())

    def test_task_with_multiple_recipients(self):
        task = send_email_to_assigned_user.apply((
            [self.user.id, self.user1.id],
            self.account.id,
            "assigned"
        ))
        self.assertEqual("SUCCESS", task.state)