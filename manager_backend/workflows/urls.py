# backend/workflows/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowViewSet, submit_workflow_view, RegisterView, LoginView, LogoutView

router = DefaultRouter()
router.register(r'', WorkflowViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('<str:workflow_id>/submit/', submit_workflow_view, name='submit_workflow'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('workflows/<str:workflow_id>/submit/', submit_workflow_view, name='submit_workflow'),

]
