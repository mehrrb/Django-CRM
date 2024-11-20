import logging
from django.utils.functional import SimpleLazyObject
from common.models import Profile

logger = logging.getLogger(__name__)

def get_profile(request):
    if not hasattr(request, '_cached_profile'):
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                request._cached_profile = Profile.objects.get(user=request.user)
                logger.debug(f"Profile found and cached: {request._cached_profile}")
            except Profile.DoesNotExist:
                request._cached_profile = None
                logger.warning(f"No profile found for user: {request.user}")
        else:
            request._cached_profile = None
            logger.debug("No authenticated user found")
    return request._cached_profile

class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.profile = SimpleLazyObject(lambda: get_profile(request))
        response = self.get_response(request)
        return response