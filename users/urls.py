from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'users'

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # Default router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path(
        'users/login/',
        views.UserViewSet.as_view({'post': 'login'}),
        name='login'
    ),
    
    path(
        'users/logout/',
        views.UserViewSet.as_view({'post': 'logout'}),
        name='logout'
    ),
    
    path(
        'users/me/',
        views.UserViewSet.as_view({'get': 'me'}),
        name='me'
    ),
    
    path(
        'users/<str:pk>/change-password/',
        views.UserViewSet.as_view({'post': 'change_password'}),
        name='change-password'
    ),
]