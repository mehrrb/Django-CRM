from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "api_tasks"

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='task')

urlpatterns = [
    # Default router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path(
        'tasks/<str:pk>/comments/',
        views.TaskViewSet.as_view({'post': 'add_comment'}),
        name='task-add-comment'
    ),
    
    path(
        'tasks/<str:pk>/attachments/',
        views.TaskViewSet.as_view({
            'post': 'add_attachment',
            'delete': 'remove_attachment'
        }),
        name='task-attachments'
    ),
    
    path(
        'tasks/<str:pk>/complete/',
        views.TaskViewSet.as_view({'post': 'complete'}),
        name='task-complete'
    ),
    
    path(
        'tasks/dashboard/',
        views.TaskViewSet.as_view({'get': 'dashboard'}),
        name='task-dashboard'
    ),
    
    path(
        'tasks/bulk-action/',
        views.TaskViewSet.as_view({'post': 'bulk_action'}),
        name='task-bulk-action'
    ),
    
    path(
        'tasks/export/',
        views.TaskViewSet.as_view({'post': 'export'}),
        name='task-export'
    ),
    
    path(
        'tasks/import/',
        views.TaskViewSet.as_view({'post': 'import_tasks'}),
        name='task-import'
    ),
]