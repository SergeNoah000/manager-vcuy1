from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('workflow/<uuid:workflow_id>/', views.tasks_by_workflow, name='tasks_by_workflow'),
    path('<uuid:task_id>/', views.task_detail, name='task_detail'),
    path('volunteer/<uuid:volunteer_id>/', views.tasks_by_volunteer, name='tasks_by_volunteer'),
]
