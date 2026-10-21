from django.urls import path
from .views import MyProfileView, DownloadUploadedCVView
from .alert_views import AlertPreferenceView, UnsubscribeView
from .cv_views import CVDraftView, CVApproveView, CVVersionDownloadView, CurrentCVDownloadView, CVVersionListView

urlpatterns = [
    path('me/alert-preferences/', AlertPreferenceView.as_view(), name='alert-preferences'),
    path('alert-unsubscribe/', UnsubscribeView.as_view(), name='alert-unsubscribe'),
    path('me/', MyProfileView.as_view(), name='my-profile'),
    path('me/generate-cv/', CurrentCVDownloadView.as_view(), name='generate-cv'),
    path('me/cv/', DownloadUploadedCVView.as_view(), name='download-uploaded-cv'),
    path('me/cv-draft/', CVDraftView.as_view(), name='cv-draft'),
    path('me/cv-draft/approve/', CVApproveView.as_view(), name='cv-approve'),
    path('me/cv-versions/', CVVersionListView.as_view(), name='cv-version-list'),
    path('me/cv-versions/<uuid:version>/download/', CVVersionDownloadView.as_view(), name='cv-version-download'),
]
