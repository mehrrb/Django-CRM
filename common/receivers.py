from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

from .models import Profile, Document, Org
from .tasks import send_email_notification, cleanup_files

logger = logging.getLogger(__name__)

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create Profile when User is created"""
    try:
        if created:
            logger.info(f"Creating profile for new user: {instance.email}")
            Profile.objects.create(
                user=instance,
            )
    except Exception as e:
        logger.error(f"Error creating profile for user {instance.email}: {str(e)}")

@receiver(post_save, sender=Profile)
def send_welcome_email(sender, instance, created, **kwargs):
    """Send welcome email when Profile is created"""
    try:
        if created and hasattr(settings, 'SEND_WELCOME_EMAIL') and settings.SEND_WELCOME_EMAIL:
            send_email_notification.delay(
                instance.user.email,
                'Welcome to Our Platform',
                'emails/welcome.html',
                {'user': instance.user}
            )
    except Exception as e:
        logger.error(f"Error sending welcome email to {instance.user.email}: {str(e)}")

@receiver(pre_delete, sender=Document)
def cleanup_document_files(sender, instance, **kwargs):
    """Clean up files when Document is deleted"""
    try:
        if instance.document_file:
            logger.info(f"Cleaning up files for document: {instance.id}")
            cleanup_files.delay(instance.document_file.path)
    except Exception as e:
        logger.error(f"Error cleaning up files for document {instance.id}: {str(e)}")

@receiver(post_save, sender=Org)
def setup_new_organization(sender, instance, created, **kwargs):
    """Setup initial settings for new Organization"""
    try:
        if created:
            logger.info(f"Setting up new organization: {instance.name}")
            # Generate API key if needed
            if not instance.api_key:
                instance.api_key = instance.generate_api_key()
                instance.save()
    except Exception as e:
        logger.error(f"Error setting up organization {instance.name}: {str(e)}") 