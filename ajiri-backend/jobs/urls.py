from django.urls import path
from .views import (
    JobListView,
    JobDetailView,
    GenerateCoverLetterView,
    ApplyToJobView,
    ApplicationListView,
    SendApplicationView,
    DismissApplicationView,
    ApplicationDocumentView,
    NotificationListView,
    MarkNotificationReadView,
    IngestFeedView,
    SweepMatchesView,
)

urlpatterns = [
    path('', JobListView.as_view(), name='job-list'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('<int:pk>/generate-cover-letter/', GenerateCoverLetterView.as_view(), name='generate-cover-letter'),
    path('<int:pk>/apply/', ApplyToJobView.as_view(), name='job-apply'),
    path('applications/', ApplicationListView.as_view(), name='application-list'),
    path('applications/<int:pk>/send/', SendApplicationView.as_view(), name='application-send'),
    path('applications/<int:pk>/dismiss/', DismissApplicationView.as_view(), name='application-dismiss'),
    path('applications/<int:pk>/documents/<str:kind>/', ApplicationDocumentView.as_view(), name='application-document'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('ingest/', IngestFeedView.as_view(), name='ingest-feed'),
    path('sweep/', SweepMatchesView.as_view(), name='sweep-matches'),
    path('notifications/<int:pk>/mark-read/', MarkNotificationReadView.as_view(), name='notification-mark-read'),
]
