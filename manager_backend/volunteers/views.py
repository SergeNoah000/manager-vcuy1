
# views.py
from rest_framework import generics
from rest_framework.response import Response
from .models import Volunteer, VolunteerTask
from tasks.models import Task
from workflows.models import Workflow
from .serializers import (
    VolunteerSerializer,
    VolunteerTaskSerializer,
    TaskWithVolunteerCountSerializer,
    TaskSerializer,
)
from django.db.models import Count

# Liste des volontaires
class VolunteerListView(generics.ListAPIView):
    queryset = Volunteer.objects.all()
    serializer_class = VolunteerSerializer

# Détails d'un volontaire
class VolunteerDetailView(generics.RetrieveAPIView):
    queryset = Volunteer.objects.all()
    serializer_class = VolunteerSerializer

# Liste des tâches d'un volontaire
class TasksByVolunteerView(generics.ListAPIView):
    serializer_class = VolunteerTaskSerializer

    def get_queryset(self):
        volunteer_id = self.kwargs['volunteer_id']
        return VolunteerTask.objects.filter(volunteer__id=volunteer_id)

# Liste des volontaires ayant participé à une tâche
class VolunteersByTaskView(generics.ListAPIView):
    serializer_class = VolunteerTaskSerializer

    def get_queryset(self):
        task_id = self.kwargs['task_id']
        return VolunteerTask.objects.filter(task__id=task_id)

# Liste des volontaires pour un workflow
class VolunteersByWorkflowView(generics.ListAPIView):
    serializer_class = VolunteerSerializer

    def get_queryset(self):
        workflow_id = self.kwargs['workflow_id']
        return Volunteer.objects.filter(
            assigned_tasks__task__workflow__id=workflow_id
        ).distinct()

# Liste des tâches d'un workflow triées par nombre de volontaires assignés
class TasksByWorkflowOrderedView(generics.ListAPIView):
    serializer_class = TaskWithVolunteerCountSerializer

    def get_queryset(self):
        workflow_id = self.kwargs['workflow_id']
        return Task.objects.filter(workflow__id=workflow_id).annotate(
            volunteer_count=Count('volunteer_tasks')
        ).order_by('-volunteer_count')

# Liste des tâches (général)
class TaskListView(generics.ListAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

# Liste des tâches d'un workflow
class TasksByWorkflowView(generics.ListAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        workflow_id = self.kwargs['workflow_id']
        return Task.objects.filter(workflow__id=workflow_id)
