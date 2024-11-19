from django.urls import path
from rest_framework.routers import SimpleRouter
from users import views


router = SimpleRouter()
router.register("users_manager",viewset=views.UsersView)

app_name = 'users'

urlpatterns = [
    path('login/', views.LoginView.as_view(),name='login'),
    path('logout/', views.LogoutView.as_view(),name='logout'),

]

urlpatterns+=router.urls