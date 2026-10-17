from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import FileResponse
from rest_framework.response import Response
from pathlib import Path
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
            response = FileResponse(cv.open('rb'), as_attachment=True, filename=Path(cv.name).name)
        except FileNotFoundError:
            return Response({'detail': 'The CV file is unavailable. Please upload it again.'}, status=404)
        response['Cache-Control'] = 'private, no-store'
        return response
