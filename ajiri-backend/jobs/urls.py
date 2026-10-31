from django.urls import path
from .analytics_views import AnalyticsChoiceView, AnalyticsEventView
from .queue_views import DeliveryTaskView
from .application_progress import ApplicationProgressView
from .saved_search_views import SavedSearchList, SavedSearchDetail, SavedSearchMatches
from .employer_views import OrganisationList, DraftList, DraftWithdraw, OrganisationReview, DraftReview, ReviewQueue
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
    RestoreApplicationView,
    ApplicationDocumentView,
    NotificationListView,
    MarkNotificationReadView,
    IngestFeedView,
    SweepMatchesView,
)

urlpatterns = [
    path('delivery-tasks/<uuid:task_id>/', DeliveryTaskView.as_view(), name='delivery-task'),
    path('analytics/choice/', AnalyticsChoiceView.as_view(), name='analytics-choice'),
    path('analytics/events/', AnalyticsEventView.as_view(), name='analytics-events'),
    path('applications/<int:pk>/progress/', ApplicationProgressView.as_view(), name='application-progress'),
    path('saved-searches/', SavedSearchList.as_view(), name='saved-search-list'),
    path('saved-searches/<uuid:pk>/', SavedSearchDetail.as_view(), name='saved-search-detail'),
    path('saved-searches/<uuid:pk>/matches/', SavedSearchMatches.as_view(), name='saved-search-matches'),
    path('employers/review-queue/', ReviewQueue.as_view(), name='employer-review-queue'),
    path('employers/organisations/', OrganisationList.as_view(), name='employer-organisations'),
    path('employers/drafts/', DraftList.as_view(), name='employer-drafts'),
    path('employers/drafts/<int:pk>/withdraw/', DraftWithdraw.as_view(), name='employer-withdraw'),
    path('employers/organisations/<int:pk>/review/', OrganisationReview.as_view(), name='employer-organisation-review'),
    path('employers/drafts/<int:pk>/review/', DraftReview.as_view(), name='employer-draft-review'),
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
    path('applications/<int:pk>/restore/', RestoreApplicationView.as_view(), name='application-restore'),
    path('applications/<int:pk>/documents/<str:kind>/', ApplicationDocumentView.as_view(), name='application-document'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('ingest/', IngestFeedView.as_view(), name='ingest-feed'),
    path('sweep/', SweepMatchesView.as_view(), name='sweep-matches'),
    path('notifications/<int:pk>/mark-read/', MarkNotificationReadView.as_view(), name='notification-mark-read'),
]
