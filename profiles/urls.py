from django.urls import path
from .views import MyProfileView, GenerateCVView

urlpatterns = [
    path('me/', MyProfileView.as_view(), name='my-profile'),
    path('me/generate-cv/', GenerateCVView.as_view(), name='generate-cv'),
]