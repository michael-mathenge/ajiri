from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from profiles.cv_views import PrivateCVView
from .models import DeliveryTask


def task_data(task):
    return {'id': task.pk, 'kind': task.kind, 'state': task.state,
        'last_error': task.last_error, 'created_at': task.created_at, 'updated_at': task.updated_at}


class DeliveryTaskView(PrivateCVView):
    def get(self, request, task_id):
        return Response(task_data(get_object_or_404(DeliveryTask, pk=task_id, owner=request.user)))
