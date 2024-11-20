import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError

from common.models import Address, Org, Profile
from common.base import BaseModel
from common.utils import COUNTRIES
from teams.models import Teams

def validate_phone_number(value):
    """Validate phone number format for Iran"""
    import re
    pattern = r'^\+98[0-9]{10}$|^0[0-9]{10}$'
    if not re.match(pattern, value):
        raise ValidationError('Invalid phone number. Valid formats: +989123456789 or 09123456789')


class Contact(BaseModel):
    STATUS_CHOICES = (
        ('new', _('New')),
        ('active', _('Active')), 
        ('inactive', _('Inactive')),
    )

    SOURCE_CHOICES = (
        ('website', _('Website')),
        ('referral', _('Referral')),
        ('other', _('Other')),
    )

    salutation = models.CharField(_("Salutation"), max_length=255, default="", blank=True)
    first_name = models.CharField(_("First name"), max_length=255)
    last_name = models.CharField(_("Last name"), max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    organization = models.CharField(_("Organization"), max_length=255, null=True)
    title = models.CharField(_("Title"), max_length=255, default="", blank=True)
    primary_email = models.EmailField(unique=True)
    secondary_email = models.EmailField(default="", blank=True)
    mobile_number = models.CharField(
        max_length=20,
        validators=[validate_phone_number],
        null=True,
        unique=True
    )
    secondary_number = PhoneNumberField(null=True, blank=True)
    department = models.CharField(_("Department"), max_length=255, null=True)
    language = models.CharField(_("Language"), max_length=255, null=True)
    do_not_call = models.BooleanField(default=False)
    address = models.ForeignKey(
        Address,
        related_name="adress_contacts",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    assigned_to = models.ManyToManyField(Profile, related_name="contact_assigned_users")
    teams = models.ManyToManyField(Teams, related_name="contact_teams")
    org = models.ForeignKey(Org, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.CharField(max_length=3, choices=COUNTRIES, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='website'
    )
    company_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        db_table = "contacts"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()
    
    @property
    def created_on(self):
        return self.created_at

    @property
    def get_team_users(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        return Profile.objects.filter(id__in=team_user_ids)

    @property
    def get_team_and_assigned_users(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.assigned_to.values_list("id", flat=True))
        user_ids = team_user_ids + assigned_user_ids
        return Profile.objects.filter(id__in=user_ids)

    @property
    def get_assigned_users_not_in_teams(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.assigned_to.values_list("id", flat=True))
        user_ids = set(assigned_user_ids) - set(team_user_ids)
        return Profile.objects.filter(id__in=list(user_ids))
