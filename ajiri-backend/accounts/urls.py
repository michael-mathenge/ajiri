from django.urls import path
from .views import RegisterView, LoginView, RefreshView, LogoutView, CSRFView
from .recovery_views import PasswordResetRequest, PasswordResetConfirm, VerificationRequest, VerificationConfirm, VerificationStatus

urlpatterns = [
    path('password-reset/request/', PasswordResetRequest.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirm.as_view(), name='password-reset-confirm'),
    path('verification/request/', VerificationRequest.as_view(), name='verification-request'),
    path('verification/confirm/', VerificationConfirm.as_view(), name='verification-confirm'),
    path('verification/status/', VerificationStatus.as_view(), name='verification-status'),
    path('csrf/', CSRFView.as_view(), name='csrf'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
