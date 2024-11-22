from rest_framework.exceptions import APIException
from django.utils.translation import gettext_lazy as _

class OrganizationNotFound(APIException):
    status_code = 404
    default_detail = _('Organization not found.')
    default_code = 'organization_not_found'

class InvalidOrganization(APIException):
    status_code = 400
    default_detail = _('Invalid organization data.')
    default_code = 'invalid_organization'

class DocumentAccessDenied(APIException):
    status_code = 403
    default_detail = _('You do not have permission to access this document.')
    default_code = 'document_access_denied'

class APISettingsError(APIException):
    status_code = 400
    default_detail = _('Invalid API settings configuration.')
    default_code = 'api_settings_error'

class ProfileNotFound(APIException):
    status_code = 404
    default_detail = _('Profile not found.')
    default_code = 'profile_not_found'