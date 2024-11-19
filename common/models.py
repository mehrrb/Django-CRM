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

from common.templatetags.common_tags import (
    is_document_file_audio,
    is_document_file_code,
    is_document_file_image,
    is_document_file_pdf,
    is_document_file_sheet,
    is_document_file_text,
    is_document_file_video,
    is_document_file_zip,
)
from common.utils import COUNTRIES, ROLES
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

class Org(BaseModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    api_key = models.TextField(
        default=generate_unique_key, unique=True, editable=False
    )
    is_active = models.BooleanField(default=True)
    # address = models.TextField(blank=True, null=True)
    # user_limit = models.IntegerField(default=5)
    # country = models.CharField(max_length=3, choices=COUNTRIES, blank=True, null=True)

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        db_table = "organization"
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.name)


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
        return  {
            'email' : self.user.email,
            'id' :  self.user.id,
            'is_active' : self.user.is_active,
            'profile_pic' : self.user.profile_pic
        }


class Comment(BaseModel):
    comment = models.TextField()
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
    attachment = models.FileField(max_length=1001, upload_to='attachments/%Y/%m/')
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

    DOCUMENT_STATUS_CHOICE = (("active", "active"), ("inactive", "inactive"))

    title = models.TextField(blank=True, null=True)
    document_file = models.FileField(upload_to=document_path, max_length=5000)
    created_by = models.ForeignKey(
        Profile,
        related_name="document_uploaded",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    status = models.CharField(
        choices=DOCUMENT_STATUS_CHOICE, max_length=64, default="active"
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
