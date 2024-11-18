from django.urls import path
from invoices import views

app_name = 'invoices'

urlpatterns = [
    path('', views.invoices_list, name='list'),
    path('create/', views.invoice_create, name='create'),
    path('<int:pk>/edit/', views.invoice_edit, name='edit'),
    path('<int:pk>/delete/', views.invoice_delete, name='delete'),
    path('<int:pk>/view/', views.invoice_view, name='view'),
    path('<int:pk>/send-mail/', views.invoice_send_mail, name='send_mail'),
    path('<int:pk>/download-pdf/', views.invoice_download_pdf, name='download_pdf'),
]
