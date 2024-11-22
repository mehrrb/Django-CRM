# Python imports
import uuid
import logging

# Django imports
from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class TimeAuditModel(models.Model):
    """To path when the record was created and last modified"""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Last Modified At"
    )

    class Meta:
        abstract = True


class UserAuditModel(models.Model):
    """To track who created and last modified the record"""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created_by",
        verbose_name="Created By",
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated_by",
        verbose_name="Last Modified By",
        null=True,
    )

    class Meta:
        abstract = True


class AuditModel(TimeAuditModel, UserAuditModel):
    """Combines both time and user audit functionality"""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            logger.debug(f"Saved {self.__class__.__name__} with audit fields")
        except Exception as e:
            logger.error(f"Error saving audit model: {str(e)}")
            raise