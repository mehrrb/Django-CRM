import jwt
import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
from common.models import Profile
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class GetProfileAndOrg:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.profile = None
            
            # Log incoming request details
            logger.debug("Middleware Processing Request:")
            logger.debug(f"Path: {request.path}")
            logger.debug(f"Headers: {request.headers}")
            
            # Skip middleware for non-API paths
            if not request.path.startswith('/api/'):
                return self.get_response(request)
            
            # Get JWT token
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    # Decode token
                    decoded = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=[settings.JWT_ALGO]
                    )
                    
                    # Get user and org IDs
                    user_id = decoded.get('user_id')
                    org_id = request.headers.get('X-Org')
                    
                    if user_id and org_id:
                        # Get and set profile
                        profile = Profile.objects.get(
                            user_id=user_id,
                            org_id=org_id,
                            is_active=True
                        )
                        request.profile = profile
                        logger.info(f"Found and set profile: {profile}")
                    
                except jwt.InvalidTokenError as e:
                    logger.error(f"Token validation error: {str(e)}")
                    return JsonResponse(
                        {"error": "Invalid token"},
                        status=401
                    )
                except Profile.DoesNotExist:
                    logger.error(f"Profile not found for user {user_id} in org {org_id}")
                    return JsonResponse(
                        {"error": "Profile not found"},
                        status=404
                    )
                except Exception as e:
                    logger.error(f"Unexpected error: {str(e)}")
                    return JsonResponse(
                        {"error": "Internal server error"},
                        status=500
                    )
            
            response = self.get_response(request)
            return response
            
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            return self.get_response(request)
