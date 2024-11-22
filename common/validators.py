from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
import magic
import os
from django.core.validators import URLValidator

def validate_organization_name(value):
    """Validate organization name"""
    if len(value) < 3:
        raise ValidationError(_('Organization name must be at least 3 characters long'))
    if re.search(r'[~\!@#\$%\^&\*\(\)\+{}\":;=]', value):
        raise ValidationError(_('Organization name contains invalid characters'))

def validate_file_extension(value):
    """Validate file extension and type"""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png', '.xlsx', '.xls']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Unsupported file extension.'))

def validate_file_size(value):
    """Validate file size (max 5MB)"""
    filesize = value.size
    if filesize > 5242880:  # 5MB
        raise ValidationError(_("The maximum file size that can be uploaded is 5MB"))

def validate_phone_number(value):
    """Validate phone number format"""
    if not re.match(r'^\+?1?\d{9,15}$', str(value)):
        raise ValidationError(_('Invalid phone number format'))

def validate_website_url(value):
    """Validate website URL format and structure"""
    if not value:
        return
    if not value.startswith(('http://', 'https://')):
        raise ValidationError(_('URL must start with http:// or https://'))
    try:
        URLValidator()(value)
    except ValidationError:
        raise ValidationError(_('Invalid URL format'))