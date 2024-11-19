from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .manager import UserManagement
import uuid

class Users(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=False,
        null=True,
        blank=True
    )
    
    objects = UserManagement()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password', 'username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email