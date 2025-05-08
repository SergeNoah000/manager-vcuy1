import json
import os
import uuid
from datetime import datetime
from .redis import RedisPubSubManager 
from django.conf import settings
# Dossier où seront stockés les request_id
REQUEST_DIR = os.path.join(settings.BASE_DIR, '.request_ids')
os.makedirs(REQUEST_DIR, exist_ok=True)

SUBMIT_WORKFLOW_CHANNEL = "SUBMIT_WORKFLOW"
SUBMIT_WORKFLOW_RESPONSE_CHANNEL = "SUBMIT_WORKFLOW_RESPONSE"

def save_request_id(request_id, workflow_id):
    """Sauvegarde le request_id et le workflow associé dans un fichier."""
    data = {
        "workflow_id": str(workflow_id),
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(os.path.join(REQUEST_DIR, f"{request_id}.json"), 'w') as f:
        json.dump(data, f)

def load_request_ids():
    """Charge tous les request_ids encore en attente de réponse."""
    ids = {}
    for file in os.listdir(REQUEST_DIR):
        if file.endswith('.json'):
            path = os.path.join(REQUEST_DIR, file)
            with open(path, 'r') as f:
                ids[file.replace('.json', '')] = json.load(f)
    return ids

def submit_workflow(workflow):
    """
    Publie un workflow au coordinateur via Redis.
    Nécessite un objet `workflow` (instance du modèle).
    """
    request_id = str(uuid.uuid4())

    message = {
        "request_id": request_id,
        "workflow_id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "workflow_type": workflow.workflow_type,
        "preferences": workflow.preferences,
        "estimated_flops": workflow.estimated_resources.get("flops", 0),
        "cpu": workflow.estimated_resources.get("cpu", 0),
        "ram": workflow.estimated_resources.get("ram", 0),
        "submitted_at": workflow.submitted_at.isoformat() if workflow.submitted_at else None
    }

    manager = RedisPubSubManager(channels=[SUBMIT_WORKFLOW_RESPONSE_CHANNEL])
    manager.connect()
    manager.publish(SUBMIT_WORKFLOW_CHANNEL, json.dumps(message))
    save_request_id(request_id, workflow.id)

    return request_id
