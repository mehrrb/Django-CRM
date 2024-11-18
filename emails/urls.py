from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import views

app_name = "emails"


urlpatterns = [
    path('', views.emails_list, name='list'),
    path('compose/', views.email_compose, name='compose'),
    path('send/', views.email_send, name='send'),
    path('email_sent/', views.email_sent, name='email_sent'),
    path('email_move_to_trash/', views.email_move_to_trash, name='email_move_to_trash'),
    path('email_delete/', views.email_delete, name='email_delete'),
    path('email_trash/', views.email_trash, name='email_trash'),
    path('email_draft/', views.email_draft, name='email_draft'),
    path('email_draft_delete/', views.email_draft_delete, name='email_draft_delete'),
    path('email_imp_list/', views.email_imp_list, name='email_imp_list'),
    path('email_mark_as_important/', views.email_mark_as_important, name='email_mark_as_important'),
    path('email_mark_as_not_important/', views.email_mark_as_not_important, name='email_mark_as_not_important'),
    path('email_sent_edit/<int:pk>/', views.email_sent_edit, name='email_sent_edit'),
    path('email_sent_delete/<int:pk>/', views.email_sent_delete, name='email_sent_delete'),
    path('email_trash_delete/<int:pk>/', views.email_trash_delete, name='email_trash_delete'),
]
