from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "emails"

# ViewSet URLs
router = DefaultRouter()
router.register('api', views.EmailViewSet, basename='email-api')

# Regular URLs
urlpatterns = [
    path('', include(router.urls)),  

]