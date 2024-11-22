from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
import logging
from .models import Document, Profile, Org
from .tasks import send_email_to_new_user, send_email_user_status

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Profile)
def profile_post_save_handler(sender, instance, created, **kwargs):
    """Handle post-save actions for Profile model"""
    try:
        if created:
            logger.info(f"New profile created: {instance.id}")
            
            # Send welcome email
            send_email_to_new_user.delay(instance.user.id)
            
            # Create default settings for new profile
            if instance.role == "ADMIN":
                logger.info(f"Creating default settings for admin: {instance.id}")
                # Add your default settings creation logic here
                
    except Exception as e:
        logger.error(f"Error in profile post save handler: {str(e)}")

@receiver(post_save, sender=Document)
def document_post_save_handler(sender, instance, created, **kwargs):
    """Handle post-save actions for Document model"""
    try:
        if created:
            logger.info(f"New document created: {instance.id}")
            
            # Notify relevant users
            if instance.shared_to.exists():
                logger.info(f"Document shared with {instance.shared_to.count()} users")
                # Add your notification logic here
                
    except Exception as e:
        logger.error(f"Error in document post save handler: {str(e)}")

@receiver(pre_delete, sender=Document)
def document_pre_delete_handler(sender, instance, **kwargs):
    """Handle pre-delete actions for Document model"""
    try:
        # Clean up associated files
        if instance.document_file:
            logger.info(f"Cleaning up file for document: {instance.id}")
            instance.document_file.delete(save=False)
            
    except Exception as e:
        logger.error(f"Error in document pre delete handler: {str(e)}")

@receiver(post_save, sender=Org)
def org_post_save_handler(sender, instance, created, **kwargs):
    """Handle post-save actions for Organization model"""
    try:
        if created:
            logger.info(f"New organization created: {instance.id}")
            
            # Create default API settings
            if not instance.api_key:
                instance.generate_api_key()
                logger.info(f"Generated API key for org: {instance.id}")
                
    except Exception as e:
        logger.error(f"Error in org post save handler: {str(e)}")