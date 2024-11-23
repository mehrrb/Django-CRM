from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
import logging
import secrets
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenGenerator(PasswordResetTokenGenerator):
    """Generate unique token for user verification"""
    
    def _make_hash_value(self, user, timestamp):
        try:
            # Create a unique hash based on user data and timestamp
            hash_value = (
                six.text_type(user.pk) +
                six.text_type(timestamp) +
                six.text_type(user.is_active)
            )
            logger.debug(f"Generated hash for user {user.pk}")
            return hash_value
            
        except Exception as e:
            logger.error(f"Error generating token: {str(e)}")
            return None

    def check_token(self, user, token):
        """
        Check if a token is valid for a given user.
        """
        try:
            result = super().check_token(user, token)
            logger.info(f"Token check for user {user.pk}: {'valid' if result else 'invalid'}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking token: {str(e)}")
            return False

def generate_key():
    """Generate a random API key"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_string = secrets.token_hex(16)
    key = f"{timestamp}{random_string}"
    
    return hashlib.sha1(key.encode()).hexdigest()

def verify_jwt_token(token):
    """Verify JWT token"""
    from rest_framework_simplejwt.tokens import AccessToken
    try:
        access_token = AccessToken(token)
        return True, access_token.payload
    except Exception:
        return False, None

# Create a single instance to be used throughout the app
account_activation_token = TokenGenerator()
