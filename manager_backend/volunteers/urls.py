from django.urls import path
from . import views
urlpatterns = [
    # CRUD de base
    path('volunteers/', views.VolunteerListView.as_view(), name='volunteer-list-create'),
    path('volunteers/<uuid:pk>/', views.VolunteerDetailView.as_view(), name='volunteer-detail'),

    # path('volunteer-tasks/', views.VolunteerTaskListCreateView.as_view(), name='volunteer-task-list-create'),
    # path('volunteer-tasks/<uuid:pk>/', views.VolunteerTaskRetrieveUpdateDestroyView.as_view(), name='volunteer-task-detail'),

    # Vues personnalisées
    path('volunteers/<uuid:volunteer_id>/tasks/', views.TasksByVolunteerView.as_view(), name='tasks-by-volunteer'),
    path('tasks/<uuid:task_id>/volunteers/', views.VolunteersByTaskView.as_view(), name='volunteers-by-task'),
    path('workflows/<uuid:workflow_id>/volunteers/', views.VolunteersByWorkflowView.as_view(), name='volunteers-by-workflow'),
    path('workflows/<uuid:workflow_id>/tasks-by-volunteer-count/', views.TasksByWorkflowSortedByVolunteersView.as_view(), name='tasks-by-volunteer-count'),
]
