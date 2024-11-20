from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "api_contacts"

router = DefaultRouter()
router.register(r'contacts', views.ContactViewSet, basename='contact')

urlpatterns = [
    # Default router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path(
        'contacts/<str:pk>/comments/',
        views.ContactViewSet.as_view({'post': 'add_comment'}),
        name='contact-add-comment'
    ),
    
    path(
        'contacts/<str:pk>/attachments/',
        views.ContactViewSet.as_view({
            'post': 'add_attachment',
            'delete': 'remove_attachment'
        }),
        name='contact-attachments'
    ),
    
    path(
        'contacts/<str:pk>/tasks/',
        views.ContactViewSet.as_view({'get': 'tasks'}),
        name='contact-tasks'
    ),
    
    path(
        'contacts/bulk-update/',
        views.ContactViewSet.as_view({'post': 'bulk_update'}),
        name='contact-bulk-update'
    ),
    
    path(
        'contacts/<str:pk>/send-email/',
        views.ContactViewSet.as_view({'post': 'send_email'}),
        name='contact-send-email'
    ),
    
    path(
        'contacts/export/',
        views.ContactViewSet.as_view({'get': 'export'}),
        name='contact-export'
    ),
    
    path(
        'contacts/import/',
        views.ContactViewSet.as_view({'post': 'import_contacts'}),
        name='contact-import'
    ),
]