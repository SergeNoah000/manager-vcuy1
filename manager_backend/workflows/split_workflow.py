

from datetime import timezone
import uuid

from workflows.models import WorkflowType, Workflow

import os
import pickle
import json
import subprocess
from tasks.models import Task, TaskStatus
from volunteers.models import Volunteer
from workflows.models import WorkflowType


from django.conf import settings


manager_host = settings.MANAGER_HOST

def get_min_volunteer_resources():
    """Retourne les ressources du volontaire le plus faible (RAM, CPU)."""
    volunteers = Volunteer.objects.all()
    if not volunteers:
        return {
            "min_cpu": 1,
            "min_ram": 512,
            "disk": 1, # en Go
        }
    return {
        "min_cpu": min(v.cpu_cores for v in volunteers),
        "min_ram": min(v.ram_mb for v in volunteers),
        "disk": min(v.disk_gb for v in volunteers),
    }

def estimate_required_shards(dataset_len, min_ram_mb):
    """Estime le nombre de shards à créer pour que chaque shard passe sur le volontaire le plus faible."""
    # Simple estimation : on suppose 10MB par exemple par échantillon
    est_sample_size_mb = 0.5
    max_samples_per_shard = int(min_ram_mb / est_sample_size_mb)
    return max(1, dataset_len // max_samples_per_shard)

def split_ml_training_workflow(workflow_instance, base_path):
    """
    Effectue le découpage pour un workflow ML_TRAINING à partir du script externe.
    """
    dataset_path = os.path.join(base_path, "data")
    input_dir = os.path.join(base_path, "inputs")
    split_script = os.path.join(base_path, "split_dataset.py")

    # Étape 1: déterminer ressources min
    min_resources = get_min_volunteer_resources()

    # Étape 2: estimer nb de shards à partir du dataset complet
    dataset = pickle.load(open(os.path.join(dataset_path, "cifar-10-batches-py", "data_batch_1"), "rb"))
    dataset_len = len(dataset["data"])
    num_shards = estimate_required_shards(dataset_len, min_resources["min_ram"])

    # Étape 3: appeler le script de découpage
    subprocess.run(["python", split_script, str(num_shards)], check=True)

    # Étape 4: création des tâches pour chaque shard
    docker_img = {
        "name": "vcuy1/ml-training-v0",
        "tag": "latest"
    }
    tasks = []
    for i in range(num_shards):
        input_size = os.path.getsize(os.path.join(input_dir, f"shard_{i}/data.pkl")) // (1024 * 1024 )  # Convertir en Mo
        if (input_size > (min_resources["disk"] * 1024)):  # Convertir Go en Mo
            print(f"Shard {i} exceeds the minimum disk requirement.")   # Convertir Go en Mo
            continue

        # Créer la tâche pour chaque shard
        task = Task.objects.create(
            workflow=workflow_instance,
            name=f"Train Shard {i}",
            description=f"Training on shard {i}",
            command="python /app/train_on_shard.py",
            parameters=[],
            input_files=[{
                "container_path": f"inputs/shard_{i}/data.pkl",
                "host_path": os.path.join(input_dir, f"shard_{i}/data.pkl"),
                "url": f"{manager_host}:1010/shard_{i}/data.pkl"
            }],
            output_files=[f"outputs/shard_{i}/model.pth"],
            status= TaskStatus.CREATED,
            parent_task=None,
            is_subtask=False,
            progress=0,
            created_at=timezone.now(),
            start_time=None,
            docker_info=docker_img,
            required_resources={
                "cpu": min_resources["min_cpu"],
                "ram": min_resources["min_ram"],
                "disk": min_resources["disk"],
            },
            estimated_max_time=300,
        )
        task.input_size = os.path.getsize(os.path.join(input_dir, f"shard_{i}/data.pkl")) // (1024 * 1024)
        task.save()
    
    # Étape 5: sauvegarder les tâches dans le workflow
    workflow_instance.tasks.add(*tasks)
    workflow_instance.save()
    return tasks




def split_workflow(id:uuid.UUID, workflow_type:WorkflowType, owner_id:uuid.UUID) -> list:
    """
    Splits a workflow into smaller tasks based on the workflow type.
    
    Args:
        id (uuid.UUID): The ID of the workflow to split.
        workflow_type (str): The type of the workflow.
        owner_id (uuid.UUID): The ID of the owner of the workflow.
    
    Returns:
        list: A list of smaller tasks created from the original workflow.
    """
    # Placeholder for actual splitting logic
    
    # Get the workflow instance
    workflow_instance = Workflow.objects.get(id=id, owner_id=owner_id)

    # verify the workflow type
    if workflow_type == WorkflowType.ML_TRAINING:
        # Split the workflow using the ML training splitting logic
        base_path = os.path.join(settings.BASE_DIR, "workflows", "examples", "distributed_training_demo")
        tasks = split_ml_training_workflow(workflow_instance, base_path)
    else:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")



