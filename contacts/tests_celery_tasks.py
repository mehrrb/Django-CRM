from datetime import datetime, timedelta
from django.test.utils import override_settings
from rest_framework.test import APITestCase
from users.models import Users
from contacts.tasks import (
    send_email_to_assigned_user,
    send_contact_email,
    send_contact_status_email,
    send_contact_deletion_email
)
from contacts.tests import ContactObjectsCreation
from common.tests import ObjectsCreation

class TestCeleryTasks(ContactObjectsCreation, APITestCase):
    def setUp(self):
        super().setUp()
        self.user = Users.objects.create_user(
            email='test@example.com',
            password='testpass',
            is_active=True
        )
        self.user_contacts_mp = Users.objects.create_user(
            email='contact_mp@example.com',
            password='testpass',
            is_active=True
        )
        self.client.force_authenticate(user=self.user)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_assigned_user_email(self):
        task = send_email_to_assigned_user.apply(
            (
                [
                    self.user.id,
                    self.user_contacts_mp.id,
                ],
                self.contact.id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_contact_email(self):
        task = send_contact_email.apply(
            (
                self.contact.id,
                [self.user.id],
                "Test Subject",
                "Test Message"
            ),
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_contact_status_email(self):
        task = send_contact_status_email.apply(
            (
                self.contact.id,
                "active",
                [self.user.id]
            ),
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_contact_deletion_email(self):
        task = send_contact_deletion_email.apply(
            (
                self.contact.id,
                [self.user.id]
            ),
        )
        self.assertEqual("SUCCESS", task.state)

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_invalid_user_id(self):
        task = send_email_to_assigned_user.apply(
            (
                [999999],  # Invalid user ID
                self.contact.id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)  # Task should complete but not send email

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_invalid_contact_id(self):
        task = send_contact_email.apply(
            (
                999999,  # Invalid contact ID
                [self.user.id],
                "Test Subject",
                "Test Message"
            ),
        )
        self.assertEqual("SUCCESS", task.state)  # Task should complete but not send email