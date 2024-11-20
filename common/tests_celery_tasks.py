from datetime import datetime, timedelta
from django.test import TestCase
from django.test.utils import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile


from accounts.tests import AccountCreateTest
from common.models import Comment, User, Document, Attachments
from common.tasks import (
    resend_activation_link_to_user,
    send_email_to_new_user,
    send_email_user_delete,
    send_email_user_mentions,
    send_email_user_status,
    send_email_user_tasks,
    send_email_user_permissions
)
from common.tests import ObjectsCreation
from contacts.tests import ContactObjectsCreation
from invoices.tests import InvoiceCreateTest
from tasks.tests import TaskCreateTest


class TestCeleryTasks(ObjectsCreation, TestCase):
    def setUp(self):
        super().setUp()
        
        # Create test document
        self.document = Document.objects.create(
            title="Test Doc",
            document=SimpleUploadedFile("test.txt", b"test content"),
            created_by=self.user
        )
        
        # Create test attachment
        self.attachment = Attachments.objects.create(
            attachment=SimpleUploadedFile("test_attach.txt", b"test content"),
            created_by=self.user
        )

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_user_email_tasks(self):
        # Test new user email
        task = send_email_to_new_user.apply(
            (self.user1.email, self.user.email),
        )
        self.assertEqual("SUCCESS", task.state)

        # Test user status email
        task = send_email_user_status.apply(
            (self.user1.id, self.user.id),
        )
        self.assertEqual("SUCCESS", task.state)

        # Test different user statuses
        statuses = [
            (False, False, True),  # inactive, no sales, marketing
            (True, False, False),  # active, no sales, no marketing
            (True, True, False),   # active, sales, no marketing
            (True, False, True)    # active, no sales, marketing
        ]
        
        for is_active, has_sales, has_marketing in statuses:
            self.user1.is_active = is_active
            self.user1.has_sales_access = has_sales
            self.user1.has_marketing_access = has_marketing
            self.user1.save()
            
            task = send_email_user_status.apply((self.user1.id,))
            self.assertEqual("SUCCESS", task.state)

        # Test user delete email
        task = send_email_user_delete.apply((self.user1.email,))
        self.assertEqual("SUCCESS", task.state)

        # Test activation link email
        task = resend_activation_link_to_user.apply((self.user1.email,))
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_user_tasks_email(self):
        task = send_email_user_tasks.apply(
            (self.user1.id, ["task1", "task2"]),
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_user_permissions_email(self):
        task = send_email_user_permissions.apply(
            (self.user1.id, ["permission1", "permission2"]),
        )
        self.assertEqual("SUCCESS", task.state)

    def test_task_error_handling(self):
        # Test with invalid user ID
        task = send_email_user_status.apply((99999,))
        self.assertEqual("SUCCESS", task.state)

        # Test with invalid email
        task = send_email_to_new_user.apply(("invalid@email.com", self.user.email))
        self.assertEqual("SUCCESS", task.state)


class TestUserMentionsForAccountComments(AccountCreateTest, TestCase):
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_user_mentions_for_account_comment(self):
        self.user_comment = User.objects.create(
            first_name="johnComment",
            username="johnDoeComment",
            email="johnDoeComment@example.com",
            role="ADMIN",
        )
        self.user_comment.set_password("password")
        self.user_comment.save()

        self.comment.comment = "content @{}".format(self.user_comment.username)
        self.comment.account = self.account
        self.comment.save()

        task = send_email_user_mentions.apply(
            (
                self.comment.id,
                "accounts",
            ),
        )
        self.assertEqual("SUCCESS", task.state)


class TestUserMentionsForContactsComments(ContactObjectsCreation, TestCase):
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_user_mentions_for_contacts_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment",
            username="johnDoeComment",
            email="johnDoeComment@example.com",
            role="ADMIN",
        )
        self.user_comment.set_password("password")
        self.user_comment.save()

        self.comment.comment = "content @{}".format(self.user_comment.username)
        self.comment.contact = self.contact
        self.comment.save()

        task = send_email_user_mentions.apply(
            (
                self.comment.id,
                "contacts",
            ),
        )
        self.assertEqual("SUCCESS", task.state)

class TestUserMentionsForTasksComments(TaskCreateTest, TestCase):
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_user_mentions_for_tasks_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment",
            username="johnDoeComment",
            email="johnDoeComment@example.com",
            role="ADMIN",
        )
        self.user_comment.set_password("password")
        self.user_comment.save()

        self.comment.comment = "content @{}".format(self.user_comment.username)
        self.comment.task = self.task
        self.comment.save()

        task = send_email_user_mentions.apply(
            (
                self.comment.id,
                "tasks",
            ),
        )
        self.assertEqual("SUCCESS", task.state)


class TestUserMentionsForInvoiceComments(InvoiceCreateTest, TestCase):
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_user_mentions_for_invoice_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment",
            username="johnDoeComment",
            email="johnDoeComment@example.com",
            role="ADMIN",
        )
        self.user_comment.set_password("password")
        self.user_comment.save()

        self.comment.comment = "content @{}".format(self.user_comment.username)
        self.comment.invoice = self.invoice
        self.comment.save()

        task = send_email_user_mentions.apply(
            (
                self.comment.id,
                "invoices",
            ),
        )
        self.assertEqual("SUCCESS", task.state)



