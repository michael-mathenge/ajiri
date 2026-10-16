from django.urls import path
from .views import RegisterView, LoginView, RefreshView, LogoutView, CSRFView

urlpatterns = [
    path('csrf/', CSRFView.as_view(), name='csrf'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
