import os
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from django.urls import include, path
from django.urls import re_path as url
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
# from drf_yasg import openapi
# from drf_yasg.views import get_schema_view
from rest_framework import permissions


app_name = "crm"

urlpatterns = [
    url(
        r"^healthz/$",
        TemplateView.as_view(template_name="healthz.html"),
        name="healthz",
    ),
    path("api/", include("common.app_urls", namespace="common_urls")),
    path(
        "logout/", views.LogoutView.as_view(), {"next_page": "/login/"}, name="logout"
    ),
    path("django/admin/", admin.site.urls),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("", include("common.urls", namespace="common")),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('contacts/', include('contacts.urls', namespace='contacts')),
    path('emails/', include('emails.urls', namespace='emails')),
    path('invoices/', include('invoices.urls', namespace='invoices')),
    path('teams/', include('teams.urls', namespace='teams')),
    path('users/', include('users.urls', namespace='users')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

