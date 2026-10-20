from django.urls import path
from .send_views import (SendPlanView, SendAuthorizationListView, SendAuthorizationView,
                         WithdrawAuthorizationView, DispatchAuthorizationView)
from .package_views import (PackageListView, PackageDraftView, PackageReviewView,
                            PackageApprovalView, PackageDocumentView)
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
    path('applications/<int:pk>/send-plan/', SendPlanView.as_view(), name='application-send-plan'),
    path('applications/<int:pk>/send-authorizations/', SendAuthorizationListView.as_view(), name='application-authorizations'),
    path('applications/<int:pk>/send-authorizations/<uuid:authorization_id>/', SendAuthorizationView.as_view(), name='application-authorization'),
    path('applications/<int:pk>/send-authorizations/<uuid:authorization_id>/withdraw/', WithdrawAuthorizationView.as_view(), name='application-authorization-withdraw'),
    path('applications/<int:pk>/send-authorizations/<uuid:authorization_id>/dispatch/', DispatchAuthorizationView.as_view(), name='application-authorization-dispatch'),
    path('', JobListView.as_view(), name='job-list'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('<int:pk>/generate-cover-letter/', GenerateCoverLetterView.as_view(), name='generate-cover-letter'),
    path('<int:pk>/apply/', ApplyToJobView.as_view(), name='job-apply'),
    path('applications/', ApplicationListView.as_view(), name='application-list'),
    path('applications/<int:pk>/packages/', PackageListView.as_view(), name='application-packages'),
    path('applications/<int:pk>/package-draft/', PackageDraftView.as_view(), name='application-package-draft'),
    path('applications/<int:pk>/packages/<uuid:package_id>/', PackageReviewView.as_view(), name='application-package-review'),
    path('applications/<int:pk>/packages/<uuid:package_id>/approve/', PackageApprovalView.as_view(), name='application-package-approve'),
    path('applications/<int:pk>/packages/<uuid:package_id>/documents/<str:kind>/', PackageDocumentView.as_view(), name='application-package-document'),
    path('applications/<int:pk>/send/', SendApplicationView.as_view(), name='application-send'),
    path('applications/<int:pk>/dismiss/', DismissApplicationView.as_view(), name='application-dismiss'),
    path('applications/<int:pk>/documents/<str:kind>/', ApplicationDocumentView.as_view(), name='application-document'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('ingest/', IngestFeedView.as_view(), name='ingest-feed'),
    path('sweep/', SweepMatchesView.as_view(), name='sweep-matches'),
    path('notifications/<int:pk>/mark-read/', MarkNotificationReadView.as_view(), name='notification-mark-read'),
]
