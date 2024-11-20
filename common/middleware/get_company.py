import jwt
import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
from common.models import Profile

logger = logging.getLogger(__name__)

class GetProfileAndOrg:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.profile = None
            
            # Log incoming request details
            logger.info("Middleware Processing Request:")
            logger.info(f"Headers: {request.headers}")
            
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
                    logger.info(f"Decoded token: {decoded}")
                    
                    user_id = decoded.get('user_id')
                    org_id = request.headers.get('org')
                    
                    logger.info(f"Looking for profile with user_id={user_id}, org_id={org_id}")
                    
                    if user_id and org_id:
                        profile = Profile.objects.get(
                            user_id=user_id,
                            org_id=org_id,
                            is_active=True
                        )
                        request.profile = profile
                        logger.info(f"Found and set profile: {profile}")
                    
                except jwt.InvalidTokenError as e:
                    logger.error(f"Token validation error: {str(e)}")
                except Profile.DoesNotExist:
                    logger.error("Profile not found")
                except Exception as e:
                    logger.error(f"Unexpected error: {str(e)}")
            
            response = self.get_response(request)
            return response
            
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            return self.get_response(request)
