from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views
from . import views

app_name = "api_common"

router = DefaultRouter()
router.register(r'common', views.CommonViewSet, basename='common')
router.register(r'profiles', views.ProfileViewSet, basename='profile')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'api-settings', views.APISettingsViewSet, basename='api-settings')

urlpatterns = [
    # Default router URLs
    path('', include(router.urls)),
    
    # JWT Authentication
    path(
        "auth/refresh-token/",
        jwt_views.TokenRefreshView.as_view(),
        name="token_refresh"
    ),
    
    # Custom endpoints mapped to ViewSet actions
    path(
        'dashboard/',
        views.CommonViewSet.as_view({'get': 'dashboard'}),
        name='dashboard'
    ),
    
    path(
        'org/',
        views.CommonViewSet.as_view({
            'get': 'org',
            'post': 'org'
        }),
        name='org'
    ),
    
    path(
        'profiles/<str:pk>/status/',
        views.ProfileViewSet.as_view({'post': 'status'}),
        name='profile-status'
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