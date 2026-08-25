from rest_framework import generics, permissions
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Job
from .serializers import JobListSerializer, JobDetailSerializer
from .filters import JobFilter
from .cover_letter_generator import generate_cover_letter_docx


class JobListView(generics.ListAPIView):
    serializer_class = JobListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = JobFilter
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False).order_by('-posted_at')


class JobDetailView(generics.RetrieveAPIView):
    serializer_class = JobDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False)


class GenerateCoverLetterView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False)

    def get(self, request, pk):
        job = get_object_or_404(self.get_queryset(), pk=pk)
        profile = request.user.profile
        buffer = generate_cover_letter_docx(profile, job)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        safe_company = job.company_name.replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="Cover_Letter_{safe_company}.docx"'
        return response