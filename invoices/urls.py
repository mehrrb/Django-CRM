from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')

urlpatterns = router.urls
