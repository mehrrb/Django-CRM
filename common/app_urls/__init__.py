from django.urls import include, path

app_name = "common_urls"

urlpatterns = [
    # Common app URLs
    path("", include("common.urls")),
    
    # Account related URLs
    path("accounts/", include("common.urls", namespace="api_accounts")),
    
    # Contact related URLs  
    path("contacts/", include("common.urls", namespace="api_contacts")),
    
    # Teams related URLs
    path("teams/", include("common.urls", namespace="api_teams")),
    
    # Documents related URLs - using common.urls instead of documents.urls
    path("documents/", include("common.urls", namespace="api_documents")),
    
    # API Settings related URLs
    path("settings/", include("common.urls", namespace="api_settings")),
]
