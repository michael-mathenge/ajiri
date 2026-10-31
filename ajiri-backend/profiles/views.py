from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import FileResponse
from rest_framework.response import Response
from pathlib import Path
from io import BytesIO
from django.conf import settings
from .models import Profile
from .serializers import ProfileSerializer


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        return self.request.user.profile


class DownloadUploadedCVView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        cv = request.user.profile.cv_file
        if not cv:
            return Response({'detail': 'No CV uploaded.'}, status=404)
        try:
            suffix = Path(cv.name).suffix.lower()
            # Only the genuine supported format is retained, never its stored UUID.
            # see docs/CONCEPTS.md#readable-document-downloads
            suffix = suffix if suffix in ('.pdf', '.doc', '.docx') else '.bin'
            if getattr(settings, 'MALWARE_SCANNING_ENABLED', False):
                from .scanner import MAX_BYTES, ScanUnavailable, require_clean
                with cv.open('rb') as stream:
                    data = stream.read(MAX_BYTES+1)
                if not 0 < len(data) <= MAX_BYTES:
                    raise ScanUnavailable()
                require_clean(data)  # Legacy bytes receive no inferred clean status.
                response = FileResponse(BytesIO(data), as_attachment=True, filename='Uploaded_CV' + suffix)
            else:
                response = FileResponse(cv.open('rb'), as_attachment=True, filename='Uploaded_CV' + suffix)
        except FileNotFoundError:
            return Response({'detail': 'The CV file is unavailable. Please upload it again.'}, status=404)
        response['Cache-Control'] = 'private, no-store'
        return response
