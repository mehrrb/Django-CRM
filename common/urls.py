from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views
from . import views

app_name = "common"

router = DefaultRouter()
router.register(r'v1/common', views.CommonViewSet, basename='common')
router.register(r'v1/profiles', views.ProfileViewSet)
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'api-settings', views.APISettingsViewSet, basename='api-settings')
router.register(r'orgs', views.OrgViewSet, basename='org')

urlpatterns = [
    # Default router URLs
    path('', include(router.urls)),
    
    # JWT token URLs
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile specific endpoints
    path(
        'profiles/<str:pk>/activate/',
        views.ProfileViewSet.as_view({'post': 'activate'}),
        name='profile-activate'
    ),
    path(
        'profiles/<str:pk>/deactivate/',
        views.ProfileViewSet.as_view({'post': 'deactivate'}),
        name='profile-deactivate'
    ),
    
    # Document specific endpoints
    path(
        'documents/<str:pk>/share/',
        views.DocumentViewSet.as_view({'post': 'share'}),
        name='document-share'
    ),
    
    # API Settings specific endpoints
    path(
        'api-settings/<str:pk>/update-tags/',
        views.APISettingsViewSet.as_view({'post': 'update_tags'}),
        name='api-settings-update-tags'
    ),
]