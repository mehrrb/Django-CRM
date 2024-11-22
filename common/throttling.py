from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle
import logging

logger = logging.getLogger(__name__)

class OrgRateThrottle(UserRateThrottle):
    """
    Throttle based on organization ID
    Limits API calls per organization
    """
    rate = '100/hour'  # Default rate
    
    def get_cache_key(self, request, view):
        try:
            if not request.profile:
                return None
                
            # Use org ID as cache key
            key = f'throttle_org_{request.profile.org.id}'
            logger.debug(f"Throttle cache key: {key}")
            return key
            
        except Exception as e:
            logger.error(f"Error in throttle: {str(e)}")
            return None

class DocumentRateThrottle(UserRateThrottle):
    """
    Specific throttle for document operations
    More restrictive than general org throttle
    """
    rate = '50/hour'
    
    def get_cache_key(self, request, view):
        try:
            if not request.profile:
                return None
                
            # Use org ID and document action as cache key    
            key = f'throttle_doc_{request.profile.org.id}_{view.action}'
            logger.debug(f"Document throttle cache key: {key}")
            return key
            
        except Exception as e:
            logger.error(f"Error in document throttle: {str(e)}")
            return None 