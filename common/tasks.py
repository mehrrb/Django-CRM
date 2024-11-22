import datetime
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import logging
from django.template.loader import render_to_string
import os

from users.models import Users as User
from common.token_generator import account_activation_token

logger = logging.getLogger(__name__)

@shared_task
def send_email_to_new_user(user_id):
    """Send Mail To Users When their account is created"""
    try:
        user_obj = User.objects.filter(id=user_id).first()
        if not user_obj:
            logger.error(f"User not found: {user_id}")
            return False

        context = {}
        user_email = user_obj.email
        context["url"] = settings.DOMAIN_NAME
        context["uid"] = urlsafe_base64_encode(force_bytes(user_obj.pk))
        context["token"] = account_activation_token.make_token(user_obj)
        
        time_delta_two_hours = datetime.datetime.strftime(
            timezone.now() + datetime.timedelta(hours=2), "%Y-%m-%d-%H-%M-%S"
        )
        activation_key = context["token"] + time_delta_two_hours
        user_obj.activation_key = activation_key
        user_obj.save()

        message = f"""
        Welcome to NetPardaz CRM!
        Please click the following link to activate your account:
        {settings.DOMAIN_NAME}/auth/activate-user/{context['uid']}/{context['token']}/{activation_key}/
        
        This link will expire in 2 hours.
        """
        
        msg = EmailMessage(
            "Welcome to NetPardaz CRM",
            message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]
        )
        result = msg.send()
        logger.info(f"Welcome email sent to {user_email}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error sending new user email: {str(e)}")
        return False

@shared_task
def send_email_user_status(user_id, changed_by_id):
    """Send email when user status changes"""
    try:
        user = User.objects.get(id=user_id)
        changed_by = User.objects.get(id=changed_by_id)
        
        status = "activated" if user.is_active else "deactivated"
        message = f"""
        Your account has been {status} by: {changed_by.email}
        You can access the system at: {settings.DOMAIN_NAME}
        """
        
        msg = EmailMessage(
            f"Account {status.title()}",
            message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        result = msg.send()
        logger.info(f"Status change email sent to {user.email}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error sending status update email: {str(e)}")
        return False

@shared_task
def send_email_notification(email, subject, template_name, context):
    """Send email notification using template"""
    try:
        message = render_to_string(template_name, context)
        msg = EmailMessage(
            subject,
            message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        result = msg.send()
        logger.info(f"Email notification sent to {email}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")
        return False

@shared_task
def cleanup_files(file_path):
    """Clean up files from storage"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted successfully: {file_path}")
            return True
        logger.warning(f"File not found: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")
        return False
