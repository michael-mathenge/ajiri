from rest_framework import generics, permissions
from .models import Job
from .serializers import JobListSerializer, JobDetailSerializer
from .filters import JobFilter


class JobListView(generics.ListAPIView):
    serializer_class = JobListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = JobFilter
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False).order_by('-posted_at')


class JobDetailView(generics.RetrieveAPIView):
    serializer_class = JobDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False)