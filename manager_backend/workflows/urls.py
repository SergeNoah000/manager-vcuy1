# backend/workflows/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowViewSet, submit_workflow_view

router = DefaultRouter()
router.register(r'', WorkflowViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('<str:workflow_id>/submit/', submit_workflow_view, name='submit_workflow'),
]
# This file defines the URL routing for the Workflow API.
# It uses Django REST Framework's router to automatically generate the URL patterns for the WorkflowViewSet.
# The WorkflowViewSet handles the CRUD operations for the Workflow model.
# The urlpatterns list includes the router's URLs, which will be prefixed with 'workflows/'.
# This means that the Workflow API will be accessible at /workflows/ in the API.
# The WorkflowViewSet is responsible for handling requests to the Workflow API.
# It uses the WorkflowSerializer to serialize and deserialize Workflow objects.