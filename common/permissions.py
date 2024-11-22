from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

class IsOrgAdmin(permissions.BasePermission):
    """
    Allow access only to organization admins
    """
    def has_permission(self, request, view):
        return request.profile and request.profile.is_organization_admin

class IsOrgMember(permissions.BasePermission):
    """
    Allow access only to organization members
    """
    def has_permission(self, request, view):
        return request.profile and request.profile.org

class CanManageDocument(permissions.BasePermission):
    """
    Allow access to:
    - Organization admins
    - Document creators
    - Team members (for shared documents)
    """
    def has_object_permission(self, request, view, obj):
        try:
            # Allow org admins
            if request.profile.is_organization_admin:
                return True
                
            # Allow document creator
            if obj.created_by == request.profile:
                return True
                
            # Allow team members
            if request.profile in obj.get_team_users:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            return False

class CanManageAPISettings(permissions.BasePermission):
    """
    Allow access to:
    - Organization admins
    - API Settings creators
    """
    def has_object_permission(self, request, view, obj):
        try:
            return (
                request.profile.is_organization_admin or 
                obj.created_by == request.profile
            )
        except Exception as e:
            logger.error(f"API Settings permission check error: {str(e)}")
            return False