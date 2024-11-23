import binascii
import datetime
import os
import time
import uuid
import arrow
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from users.models import Users as User

from common.utils import (
    is_document_file_audio,
    is_document_file_code,
    is_document_file_image,
    is_document_file_pdf,
    is_document_file_sheet,
    is_document_file_text,
    is_document_file_video,
    is_document_file_zip,
    COUNTRIES,
    ROLES
)
from common.base import BaseModel


def img_url(self, filename):
    hash_ = int(time.time())
    return "%s/%s/%s" % ("profile_pics", hash_, filename)


class Address(BaseModel):
    address_line = models.CharField(
        _("Address"), max_length=255, blank=True, default=""
    )
    street = models.CharField(_("Street"), max_length=55, blank=True, default="")
    city = models.CharField(_("City"), max_length=255, blank=True, default="")
    state = models.CharField(_("State"), max_length=255, blank=True, default="")
    postcode = models.CharField(
        _("Post/Zip-code"), max_length=64, blank=True, default=""
    )
    country = models.CharField(max_length=3, choices=COUNTRIES, blank=True, default="")

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        db_table = "address"
        ordering = ("-created_at",)

    def __str__(self):
        return self.city if self.city else ""

    def get_complete_address(self):
        address = ""
        if self.address_line:
            address += self.address_line
        if self.street:
            if address:
                address += ", " + self.street
            else:
                address += self.street
        if self.city:
            if address:
                address += ", " + self.city
            else:
                address += self.city
        if self.state:
            if address:
                address += ", " + self.state
            else:
                address += self.state
        if self.postcode:
            if address:
                address += ", " + self.postcode
            else:
                address += self.postcode
        if self.country:
            if address:
                address += ", " + self.get_country_display()
            else:
                address += self.get_country_display()
        return address

def generate_unique_key():
    return str(uuid.uuid4())

from django.db import models
from users.models import Users as User


class Org(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="default name")
    address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="org_user")
    country = models.CharField(max_length=100, null=True, blank=True)
    api_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    profiles = models.ManyToManyField(
        'Users',
        through='Profile',
        related_name='organizations'
    )

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        db_table = "organization"
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.name)

    def get_active_profiles(self):
        return self.profile_set.filter(is_active=True)
    
    def get_admin_profiles(self):
        return self.profile_set.filter(is_organization_admin=True)
    
    @property
    def total_documents(self):
        return self.document_set.count()

    def generate_api_key(self):
        """Generate a random API key"""
        return binascii.hexlify(os.urandom(20)).decode()

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = self.generate_api_key()
        super().save(*args, **kwargs)

    @property
    def profiles(self):
        return self.profile_set.all()


class Profile(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    org = models.ForeignKey(
        Org, null=True, on_delete=models.CASCADE, blank=True, related_name="user_org"
    )
    phone = PhoneNumberField(null=True, unique=True)
    alternate_phone = PhoneNumberField(null=True,blank=True)
    address = models.ForeignKey(
        Address,
        related_name="adress_users",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    role = models.CharField(max_length=50, choices=ROLES, default="USER")
    has_sales_access = models.BooleanField(default=False)
    has_marketing_access = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_organization_admin = models.BooleanField(default=False)
    date_of_joining = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        db_table = "profile"
        ordering = ("-created_at",)
        unique_together = ["user", "org"]

    def __str__(self):
        return f"{self.user.email} <{self.org.name}>"

    @property
    def is_admin(self):
        return self.is_organization_admin

    @property
    def user_details(self):
        return {
            'email': self.user.email,
            'id': self.user.id,
            'is_active': self.user.is_active
        }


class Comment(BaseModel):
    comment = models.CharField(max_length=255)
    user = models.ForeignKey(
        User,
        related_name="user_comments",
        on_delete=models.CASCADE,
        null=True,
    )
    org = models.ForeignKey(
        Org, 
        related_name="org_comments",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    account = models.ForeignKey(
        'accounts.Account',
        blank=True,
        null=True,
        related_name="accounts_comments",
        on_delete=models.CASCADE
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        blank=True,
        null=True,
        related_name="contact_comments",
        on_delete=models.CASCADE
    )
    invoice = models.ForeignKey(
        'invoices.Invoice',
        blank=True,
        null=True,
        related_name="invoice_comments",
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.comment

class Attachments(BaseModel):
    file_name = models.CharField(max_length=60)
    attachment = models.FileField(max_length=1001, upload_to='attachments/')
    account = models.ForeignKey(
        'accounts.Account',
        blank=True,
        null=True,
        related_name='account_attachment',
        on_delete=models.CASCADE
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        blank=True,
        null=True,
        related_name='contact_attachment',
        on_delete=models.CASCADE
    )
    invoice = models.ForeignKey(
        'invoices.Invoice',
        blank=True,
        null=True,
        related_name='invoice_attachment',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.file_name


def document_path(self, filename):
    hash_ = int(time.time())
    return "%s/%s/%s" % ("docs", hash_, filename)


class Document(BaseModel):
    DOCUMENT_STATUS_CHOICE = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("deleted", "Deleted"),
    )

    title = models.CharField(
        _("Title"), 
        max_length=100, 
        default="Untitled Document"
    )
    document_file = models.FileField(
        _("Document"), 
        upload_to='documents/',
        null=True,
        blank=True
    )
    status = models.CharField(
        _("Status"),
        choices=DOCUMENT_STATUS_CHOICE, 
        max_length=64, 
        default="active"
    )
    description = models.TextField(
        _("Description"), 
        blank=True, 
        null=True
    )
    created_by = models.ForeignKey(
        Profile,
        related_name="document_uploaded",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    shared_to = models.ManyToManyField(Profile, related_name="document_shared_to")
    teams = models.ManyToManyField("teams.Teams", related_name="document_teams")
    org = models.ForeignKey(
        Org,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_org",
    )

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        db_table = "document"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title}"
 
    def file_type(self):
        name_ext_list = self.document_file.url.split(".")
        if len(name_ext_list) > 1:
            ext = name_ext_list[int(len(name_ext_list) - 1)]
            if is_document_file_audio(ext):
                return ("audio", "fa fa-file-audio")
            if is_document_file_video(ext):
                return ("video", "fa fa-file-video")
            if is_document_file_image(ext):
                return ("image", "fa fa-file-image")
            if is_document_file_pdf(ext):
                return ("pdf", "fa fa-file-pdf")
            if is_document_file_code(ext):
                return ("code", "fa fa-file-code")
            if is_document_file_text(ext):
                return ("text", "fa fa-file-alt")
            if is_document_file_sheet(ext):
                return ("sheet", "fa fa-file-excel")
            if is_document_file_zip(ext):
                return ("zip", "fa fa-file-archive")
            return ("file", "fa fa-file")
        return ("file", "fa fa-file")

    @property
    def get_team_users(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        return Profile.objects.filter(id__in=team_user_ids)

    @property
    def get_team_and_assigned_users(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.shared_to.values_list("id", flat=True))
        user_ids = team_user_ids + assigned_user_ids
        return Profile.objects.filter(id__in=user_ids)

    @property
    def get_assigned_users_not_in_teams(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.shared_to.values_list("id", flat=True))
        user_ids = set(assigned_user_ids) - set(team_user_ids)
        return Profile.objects.filter(id__in=list(user_ids))

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()


def generate_key():
    return binascii.hexlify(os.urandom(8)).decode()


class APISettings(BaseModel):
    title = models.TextField()
    apikey = models.CharField(max_length=16, blank=True)
    website = models.URLField(max_length=255, null=True)
    lead_assigned_to = models.ManyToManyField(
        Profile, related_name="lead_assignee_users"
    )
    tags = models.ManyToManyField("accounts.Tags", blank=True)
    created_by = models.ForeignKey(
        Profile,
        related_name="settings_created_by",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    org = models.ForeignKey(
        Org,
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
        related_name="org_api_settings",
    )
    

    class Meta:
        verbose_name = "APISetting"
        verbose_name_plural = "APISettings"
        db_table = "apiSettings"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title}"
    

    def save(self, *args, **kwargs):
        if not self.apikey or self.apikey is None or self.apikey == "":
            self.apikey = generate_key()
        super().save(*args, **kwargs)
