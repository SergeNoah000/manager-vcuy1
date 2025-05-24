

import uuid

from workflows.models import WorkflowType, Workflow

import os
import pickle
from tasks.models import Task, TaskStatus
from volunteers.models import Volunteer
from workflows.models import WorkflowType
import logging
import tarfile
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)
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

def download_cifar10_if_needed(dataset_path):
    cifar10_dir = os.path.join(dataset_path, "cifar-10-batches-py")
    archive_path = os.path.join(dataset_path, "cifar-10-python.tar.gz")

    if os.path.exists(cifar10_dir):
        return  # Déjà extrait

    if not os.path.exists(archive_path):
        logger.warning(f"⬇️ Téléchargement du dataset CIFAR-10 sur {archive_path}")
        url = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
        urllib.request.urlretrieve(url, archive_path)

    logger.warning(f"📦 Extraction du dataset CIFAR-10 sur {archive_path}")
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=dataset_path)

def split_ml_training_workflow(workflow_instance: Workflow, base_path, logger:logging.Logger):
    """
    Effectue le découpage pour un workflow ML_TRAINING à partir du script externe.
    """
    dataset_path = os.path.join(base_path, "data")
    input_dir = os.path.join(base_path, "inputs")
    split_script = os.path.join(base_path, "split_dataset.py")

    # S'assurer que le dataset est présent
    download_cifar10_if_needed(dataset_path)

    # Étape 1: déterminer ressources min
    min_resources = get_min_volunteer_resources()

    # Étape 2: estimer nb de shards à partir du dataset complet
    data_batch_path = os.path.join(dataset_path, "cifar-10-batches-py", "data_batch_1")
    with open(data_batch_path, "rb") as f:
        dataset = pickle.load(f, encoding='bytes')
    dataset_len = len(dataset[b"data"])

    num_shards = estimate_required_shards(dataset_len, min_resources["min_ram"])
    
    # Étape 3: appeler le script de découpage
    from workflows.examples.distributed_training_demo.split_dataset import split_dataset
    logger.warning(f"Appel de la fonction de decouppage de ml. Dataset path: {dataset_path}, Output path: {base_path}")
    # Utiliser le chemin du dataset pour l'entrée et le chemin de base pour la sortie
    split_dataset(num_shards, path=base_path, dataset_path=dataset_path, logger=logger)
    logger.warning("Decouppage Ok.")
    logger.warning("Creation de taches.")

    # Étape 4: création des tâches pour chaque shard
    docker_img = {
        "name": "traning-test",
        "tag": "latest"
    }
    tasks = []
    for i in range(num_shards):
        input_size = os.path.getsize(os.path.join(input_dir, f"shard_{i}/data.pkl")) // (1024 * 1024 )  # Convertir en Mo
        if (input_size > (min_resources["disk"] * 1024)):  # Convertir Go en Mo
            logger.info(f"Shard {i} exceeds the minimum disk requirement.")   # Convertir Go en Mo
            continue

        # Créer la tâche pour chaque shard
        task = Task.objects.create(
            workflow=workflow_instance,
            name=f"Train Shard {i}",
            description=f"Training on shard {i}",
            command="python train_on_shard.py",
            parameters=[],
            input_files=[f"shard_{i}/data.pkl"],
            output_files=[f"shard_{i}/output/model.pth", f"shard_{i}/output/metrics.json"],
            status= TaskStatus.CREATED,
            parent_task=None,
            is_subtask=False,
            progress=0,
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




def split_workflow(id:uuid.UUID, workflow_type:WorkflowType, logger) -> list:
    """
    Splits a workflow into smaller tasks based on the workflow type.
    
    Args:
        id (uuid.UUID): The ID of the workflow to split.
        workflow_type (WorkflowType): The type of the workflow.
    
    Returns:
        list: A list of smaller tasks created from the original workflow.
    """
    # Placeholder for actual splitting logic
    
    # Get the workflow instance
    workflow_instance = Workflow.objects.get(id=id)

    # verify the workflow type
    if workflow_type == WorkflowType.ML_TRAINING:
        # Split the workflow using the ML training splitting logic
        base_path = workflow_instance.executable_path
        tasks = split_ml_training_workflow(workflow_instance, base_path, logger)
    else:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")

    return tasks
