from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def sales_access_required(function):
    """Decorator to check if user has sales access"""
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            if (request.profile.role == "ADMIN" or 
                request.profile.is_superuser or 
                request.profile.has_sales_access):
                return function(request, *args, **kwargs)
            
            logger.warning(f"Sales access denied for user {request.profile.user.email}")
            raise PermissionDenied
            
        except Exception as e:
            logger.error(f"Error checking sales access: {str(e)}")
            raise PermissionDenied
    return wrap

def marketing_access_required(function):
    """Decorator to check if user has marketing access"""
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            if (request.profile.role == "ADMIN" or 
                request.profile.is_superuser or 
                request.profile.has_marketing_access):
                return function(request, *args, **kwargs)
            
            logger.warning(f"Marketing access denied for user {request.profile.user.email}")
            raise PermissionDenied
            
        except Exception as e:
            logger.error(f"Error checking marketing access: {str(e)}")
            raise PermissionDenied
    return wrap

class SalesAccessRequiredMixin(AccessMixin):
    """Mixin to check if user has sales access"""
    def dispatch(self, request, *args, **kwargs):
        try:
            if not request.profile.is_authenticated:
                return self.handle_no_permission()
                
            self.raise_exception = True
            if (request.profile.role == "ADMIN" or 
                request.profile.is_superuser or 
                request.profile.has_sales_access):
                return super().dispatch(request, *args, **kwargs)
                
            logger.warning(f"Sales access denied for user {request.profile.user.email}")
            return self.handle_no_permission()
            
        except Exception as e:
            logger.error(f"Error in sales access mixin: {str(e)}")
            return self.handle_no_permission()

class MarketingAccessRequiredMixin(AccessMixin):
    """Mixin to check if user has marketing access"""
    def dispatch(self, request, *args, **kwargs):
        try:
            if not request.profile.is_authenticated:
                return self.handle_no_permission()
                
            self.raise_exception = True
            if (request.profile.role == "ADMIN" or 
                request.profile.is_superuser or 
                request.profile.has_marketing_access):
                return super().dispatch(request, *args, **kwargs)
                
            logger.warning(f"Marketing access denied for user {request.profile.user.email}")
            return self.handle_no_permission()
            
        except Exception as e:
            logger.error(f"Error in marketing access mixin: {str(e)}")
            return self.handle_no_permission()

def admin_login_required(function):
    """this function is a decorator used to authorize if a user is admin"""

    def wrap(request, *args, **kwargs):
        if request.user.role == "ADMIN" or request.user.is_superuser:
            return function(request, *args, **kwargs)
        raise PermissionDenied

    return wrap
