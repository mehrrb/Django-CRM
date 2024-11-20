from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "api_teams"

router = DefaultRouter()
router.register(r'teams', views.TeamViewSet, basename='team')

urlpatterns = [
    # Default router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path(
        'teams/<str:pk>/add-users/',
        views.TeamViewSet.as_view({'post': 'add_users'}),
        name='team-add-users'
    ),
    
    path(
        'teams/<str:pk>/remove-users/',
        views.TeamViewSet.as_view({'post': 'remove_users'}),
        name='team-remove-users'
    ),
    
    path(
        'teams/my-teams/',
        views.TeamViewSet.as_view({'get': 'my_teams'}),
        name='my-teams'
    ),
    
    path(
        'teams/bulk-action/',
        views.TeamViewSet.as_view({'post': 'bulk_action'}),
        name='team-bulk-action'
    ),
]