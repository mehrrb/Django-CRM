import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from crum import get_current_user
import logging

from common.mixins import AuditModel

logger = logging.getLogger(__name__)

class BaseModel(AuditModel):
    """Base model for all models in the project"""
    
    id = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False, 
        db_index=True, 
        primary_key=True,
        verbose_name=_("ID")
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        try:
            user = get_current_user()
            if user is None or user.is_anonymous:
                self.created_by = None
                self.updated_by = None
            else:
                # Check if the model is being created or updated
                if self._state.adding:
                    # If created only set created_by value
                    self.created_by = user
                    self.updated_by = None
                else:
                    # If updated only set updated_by value
                    self.updated_by = user
                    
            logger.debug(f"Saving {self.__class__.__name__} with user: {user}")
            super().save(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error saving {self.__class__.__name__}: {str(e)}")
            raise

    def __str__(self):
        return str(self.id)