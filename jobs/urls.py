from django.urls import path
from .views import (
    JobListView,
    JobDetailView,
    GenerateCoverLetterView,
    ApplyToJobView,
    SendApplicationView,
)

urlpatterns = [
    path('', JobListView.as_view(), name='job-list'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('<int:pk>/generate-cover-letter/', GenerateCoverLetterView.as_view(), name='generate-cover-letter'),
    path('<int:pk>/apply/', ApplyToJobView.as_view(), name='job-apply'),
    path('applications/<int:pk>/send/', SendApplicationView.as_view(), name='application-send'),
]