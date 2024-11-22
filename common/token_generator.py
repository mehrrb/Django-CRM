from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
import logging

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

# Create a single instance to be used throughout the app
account_activation_token = TokenGenerator()
