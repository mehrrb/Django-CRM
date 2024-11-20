from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "api_accounts"

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'tags', views.TagsViewSet, basename='tags')

urlpatterns = [
    # Default router URLs
    path('', include(router.urls)),

    # Custom endpoints for accounts
    path(
        'accounts/<str:pk>/add-comment/',
        views.AccountViewSet.as_view({'post': 'add_comment'}),
        name='account-add-comment'
    ),
    
    path(
        'accounts/<str:pk>/add-attachment/',
        views.AccountViewSet.as_view({'post': 'add_attachment'}),
        name='account-add-attachment'
    ),
    
    path(
        'accounts/<str:pk>/remove-attachment/',
        views.AccountViewSet.as_view({'delete': 'remove_attachment'}),
        name='account-remove-attachment'
    ),
    
    path(
        'accounts/bulk-action/',
        views.AccountViewSet.as_view({'post': 'bulk_action'}),
        name='account-bulk-action'
    ),
    
    path(
        'accounts/<str:pk>/update-tags/',
        views.AccountViewSet.as_view({'post': 'update_tags'}),
        name='account-update-tags'
    ),
    
    path(
        'accounts/<str:pk>/email/',
        views.AccountViewSet.as_view({
            'get': 'email',
            'post': 'email'
        }),
        name='account-email'
    ),
]