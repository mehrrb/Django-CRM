from datetime import datetime, timedelta
from django.test import TestCase
from django.test.utils import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from emails.models import Email
from accounts.tasks import (
    send_email,
    send_email_to_assigned_user,
    send_scheduled_emails,
    send_account_status_email,
    send_account_deleted_email
)
from accounts.tests import AccountCreateTest
from contacts.models import Contact
from users.models import Users
from accounts.models import Account, Tags
from common.models import Attachments, Comment
from teams.models import Teams

class TestCeleryTasks(AccountCreateTest, TestCase):
    def setUp(self):
        super().setUp()
        
        # Create account
        self.account = Account.objects.create(
            name="Test Account",
            email="account@test.com", 
            created_by=self.user,
            org=self.org
        )

        # Create scheduled email
        self.email_scheduled = Email.objects.create(
            message_subject="message subject",
            message_body="message body", 
            scheduled_later=True,
            timezone="Asia/Kolkata",
            from_account=self.account,
            scheduled_date_time=(datetime.now() - timedelta(minutes=5)),
            from_email="from@email.com",
        )
        self.email_scheduled.recipients.add(self.contact.id, self.contact_user1.id)

        # Create team
        self.team = Teams.objects.create(
            name="Test Team",
            created_by=self.user,
            org=self.org
        )
        self.team.users.add(self.user, self.user1)

        # Create tags
        self.tag = Tags.objects.create(
            name="Test Tag",
            created_by=self.user,
            org=self.org
        )
        self.account.tags.add(self.tag)

        # Create attachment
        self.attachment = Attachments.objects.create(
            attachment=SimpleUploadedFile("test.txt", b"test content"),
            created_by=self.user,
            account=self.account
        )

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_scheduled_emails(self):
        task = send_scheduled_emails.apply()
        self.assertEqual("SUCCESS", task.state)

        # Test with past scheduled date
        self.email_scheduled.scheduled_date_time = datetime.now() - timedelta(days=1)
        self.email_scheduled.save()
        task = send_scheduled_emails.apply()
        self.assertEqual("SUCCESS", task.state)

        # Test with future scheduled date
        self.email_scheduled.scheduled_date_time = datetime.now() + timedelta(days=1)
        self.email_scheduled.save()
        task = send_scheduled_emails.apply()
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_send_email(self):
        task = send_email.apply((self.email_scheduled.id,))
        self.assertEqual("SUCCESS", task.state)

        # Test with invalid email ID
        task = send_email.apply((99999,))
        self.assertEqual("SUCCESS", task.state)

        # Test with attachments
        task = send_email.apply((self.email_scheduled.id,))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_assigned_user_email(self):
        task = send_email_to_assigned_user.apply(
            (
                [self.user.id, self.user1.id],
                self.account.id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)

        # Test with invalid user IDs
        task = send_email_to_assigned_user.apply(
            ([99999], self.account.id),
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_account_status_email(self):
        task = send_account_status_email.apply(
            (self.account.id, "active", [self.user.id])
        )
        self.assertEqual("SUCCESS", task.state)

        # Test with invalid account ID
        task = send_account_status_email.apply(
            (99999, "active", [self.user.id])
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_account_deleted_email(self):
        task = send_account_deleted_email.apply(
            (self.account.id, [self.user.id])
        )
        self.assertEqual("SUCCESS", task.state)

    def test_task_error_handling(self):
        with self.assertRaises(Email.DoesNotExist):
            send_email.apply((99999,))

        with self.assertRaises(Users.DoesNotExist):
            send_email_to_assigned_user.apply(([99999], self.account.id))

        with self.assertRaises(Account.DoesNotExist):
            send_account_status_email.apply((99999, "active", [self.user.id]))

    def test_task_with_attachments(self):
        task = send_email.apply((self.email_scheduled.id,))
        self.assertEqual("SUCCESS", task.state)
        self.assertTrue(self.attachment in self.account.attachments.all())

    def test_task_with_multiple_recipients(self):
        task = send_email_to_assigned_user.apply(
            ([self.user.id, self.user1.id], self.account.id)
        )
        self.assertEqual("SUCCESS", task.state)

    def test_scheduled_email_timezone(self):
        # Test different timezones
        timezones = ["UTC", "US/Pacific", "Europe/London", "Asia/Tokyo"]
        for tz in timezones:
            self.email_scheduled.timezone = tz
            self.email_scheduled.save()
            task = send_scheduled_emails.apply()
            self.assertEqual("SUCCESS", task.state)