import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
import logging
from common.models import Org, Profile, User

logger = logging.getLogger(__name__)

def verify_jwt_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGO]
        )
        logger.debug(f"Token verified successfully: {payload}")
        return True, payload
    except jwt.ExpiredSignatureError:
        logger.error("JWT token expired")
        return False, "Token expired"
    except jwt.InvalidTokenError:
        logger.error("Invalid JWT token")
        return False, "Invalid token"
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}")
        return False, "Token verification failed"

class CustomDualAuthentication(BaseAuthentication):
    """
    Custom authentication that supports both JWT and API key
    """
    def authenticate(self, request):
        try:
            jwt_user = None
            profile = None

            # Check JWT authentication
            jwt_token = request.headers.get('Authorization', '').split(' ')[1] if 'Authorization' in request.headers else None
            if jwt_token:
                is_valid, jwt_payload = verify_jwt_token(jwt_token)
                if is_valid:
                    jwt_user = User.objects.get(id=jwt_payload['user_id'])
                    if jwt_payload['user_id'] and request.headers.get("org"):
                        profile = Profile.objects.get(
                            user_id=jwt_payload['user_id'], 
                            org_id=request.headers.get("org"), 
                            is_active=True
                        )
                        request.profile = profile

            # Check API key authentication
            api_key = request.headers.get('Token')
            if api_key:
                try:
                    organization = Org.objects.get(api_key=api_key)
                    request.META['org'] = organization.id
                    profile = Profile.objects.filter(
                        org=organization, 
                        role="ADMIN"
                    ).first()
                    request.profile = profile
                    return profile.user, True
                except Org.DoesNotExist:
                    logger.error(f"Invalid API key: {api_key}")
                    raise AuthenticationFailed('Invalid API Key')

            return jwt_user or (profile.user if profile else None), True

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationFailed(str(e))
