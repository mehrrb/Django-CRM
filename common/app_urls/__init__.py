from django.urls import include, path

app_name = "common_urls"
urlpatterns = [
    path("", include(("common.urls"))),
    path("accounts/", include("accounts.urls", namespace="api_accounts")),
    path("contacts/", include("contacts.urls", namespace="api_contacts")),
]
