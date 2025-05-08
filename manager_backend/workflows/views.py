# backend/workflows/views.py
from datetime import timezone
import json
import os
import uuid

from django.conf import settings
from rest_framework import viewsets
from communication.PubSub.get_redis_instance import get_redis_manager
from .models import Workflow
from .serializers import WorkflowSerializer
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all().order_by('-created_at')
    serializer_class = WorkflowSerializer
    permission_classes = [AllowAny]  # Allow any user to access this view



def submit_workflow_view(request, workflow_id):
    """
    View to submit a workflow for processing.
    """
    try:
        workflow = get_object_or_404(Workflow, id=workflow_id)
        # Check if the workflow is in a valid state for submission
        if workflow.status != Workflow.WorkflowStatus.CREATED:
            return JsonResponse({'error': 'Workflow is not in a valid state for submission.'}, status=400)

        # submit the workflow in WORKFLOW_SUBMITTED channel
        pubsub_manager = get_redis_manager()
        data = {
            # All workflow data
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'workflow_description': workflow.description,
            'workflow_status': workflow.status,
            'created_at': workflow.created_at,
            'workflow_type': workflow.workflow_type,
            'owner': {
                'username': workflow.owner.username,
                'email': workflow.owner.email
            },
            "priority": workflow.priority,
            "estimated_resources": workflow.estimated_resources,
            "max_execution_time": workflow.max_execution_time,
            "input_data_size": workflow.input_data_size,
            "retry_count": workflow.retry_count,
            "submitted_at": timezone.now(),
        }

        # Add manager_id to the data
        with open(os.path.join(settings.BASE_DIR, ".manager_app", "manager_info.json")) as f:
            manager_info = json.load(f)
        data["manager_id"] = manager_info.get("manager_id")

        # Add request_id to the data 
        request_id = str(uuid.uuid4())
        data["request_id"] = request_id

        # Publish the workflow submission message
        pubsub_manager.publish("WORKFLOW_SUBMISSION", json.dumps(data))
        print(f"[INFO] Workflow submission message published with request_id: {request_id}")
        # Save the request_id in the .manager_app/registration_request_id.json file
        registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "registration_request_id.json")
        with open(registration_request_id_path, "w") as f:
            json.dump({"request_id": request_id}, f)
        print(f"[INFO] request_id saved in {registration_request_id_path}")


        # Update the workflow status to SUBMITTED
        workflow.status = Workflow.WorkflowStatus.SUBMITTED
        workflow.submitted_at = timezone.now()

        # Save the workflow instance
        workflow.save()
        # Perform any additional processing needed for the workflow submission
        # For example, you might want to send a notification or trigger a background task

        return JsonResponse({'message': 'Workflow submitted successfully.'}, status=200)
    except Workflow.DoesNotExist:
        return JsonResponse({'error': 'Workflow not found.'}, status=404)
