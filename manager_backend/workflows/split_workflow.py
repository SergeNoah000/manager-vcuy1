# manager_backend/workflows/split_workflow_ml.py
import os
import uuid
import json
from datetime import timezone
import pickle
import subprocess
from django.conf import settings

from workflows.models import Workflow, WorkflowStatus, WorkflowType
from tasks.models import Task, TaskStatus
from volunteers.models import Volunteer
from workflows.utils.docker_manager import get_docker_manager

# URL du manager pour les fichiers partagés
manager_host = settings.MANAGER_HOST

def get_min_volunteer_resources():
    """Retourne les ressources du volontaire le plus faible (RAM, CPU)."""
    volunteers = Volunteer.objects.all()
    if not volunteers:
        return {
            "min_cpu": 1,
            "min_ram": 512,
            "min_disk": 1, # en Go
        }
    return {
        "min_cpu": min(v.cpu_cores for v in volunteers),
        "min_ram": min(v.ram_mb for v in volunteers),
        "min_disk": min(v.disk_gb for v in volunteers),
    }

def estimate_required_shards(dataset_len, min_ram_mb):
    """Estime le nombre de shards à créer pour que chaque shard passe sur le volontaire le plus faible."""
    # Simple estimation : on suppose 0.5MB par échantillon (valeur ajustable)
    est_sample_size_mb = 0.5
    max_samples_per_shard = int(min_ram_mb / est_sample_size_mb)
    return max(1, dataset_len // max_samples_per_shard)

def containerize_task(task_id, workflow_type, script_path, base_path):
    """
    Crée un conteneur Docker pour une tâche spécifique.
    
    Args:
        task_id (str): ID de la tâche
        workflow_type (str): Type de workflow
        script_path (str): Chemin vers le script principal
        base_path (str): Chemin de base pour les scripts et données
        
    Returns:
        str: Nom complet de l'image Docker
    """
    try:
        # Obtenir le gestionnaire Docker
        docker_manager = get_docker_manager()
        
        # Déterminer l'image de base selon le type de workflow
        if workflow_type == WorkflowType.ML_TRAINING:
            base_image = "python:3.10-slim"
        else:
            base_image = "python:3.10-slim"  # Image par défaut
        
        # Construire et pousser l'image
        success, image_name = docker_manager.build_and_push_task_image(
            task_id, script_path, base_image
        )
        
        if not success:
            raise Exception(f"Échec de création de l'image Docker: {image_name}")
        
        return image_name
    except Exception as e:
        print(f"[ERROR] Erreur lors de la conteneurisation: {str(e)}")
        raise

def split_ml_training_workflow(workflow_instance, base_path):
    """
    Effectue le découpage pour un workflow ML_TRAINING à partir du script externe.
    """
    try:
        # Chemins des répertoires
        dataset_path = os.path.join(base_path, "data")
        input_dir = os.path.join(base_path, "inputs")
        output_dir = os.path.join(base_path, "outputs")
        split_script = os.path.join(base_path, "split_dataset.py")
        train_script = os.path.join(base_path, "train_on_shard.py")
        
        # S'assurer que les répertoires existent
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Étape 1: déterminer ressources min
        min_resources = get_min_volunteer_resources()
        print(f"[INFO] Ressources minimales: {min_resources}")
        
        # Étape 2: estimer nb de shards à partir du dataset
        try:
            # Vérifier si CIFAR-10 est déjà téléchargé
            if not os.path.exists(os.path.join(dataset_path, "cifar-10-batches-py")):
                print("[INFO] Dataset CIFAR-10 non trouvé, téléchargement en cours...")
            
            # Exécuter le script de division
            print(f"[INFO] Exécution du script de division: {split_script}")
            
            # Estimer le nombre de shards
            num_shards = 5  # Valeur par défaut si estimation échoue
            try:
                # Chargement du batch 1 pour estimer la taille des données
                if os.path.exists(os.path.join(dataset_path, "cifar-10-batches-py", "data_batch_1")):
                    dataset = pickle.load(open(os.path.join(dataset_path, "cifar-10-batches-py", "data_batch_1"), "rb"))
                    dataset_len = len(dataset["data"])
                    num_shards = estimate_required_shards(dataset_len, min_resources["min_ram"])
                    print(f"[INFO] Nombre de shards estimé: {num_shards}")
            except Exception as e:
                print(f"[WARNING] Estimation du nombre de shards échouée: {str(e)}")
                print(f"[INFO] Utilisation de la valeur par défaut: {num_shards} shards")
            
            # Étape 3: appeler le script de découpage
            subprocess.run([
                "python", split_script, str(num_shards)
            ], check=True, cwd=base_path)
            
            print(f"[INFO] Découpage terminé avec succès. {num_shards} shards créés.")
        except Exception as e:
            print(f"[ERROR] Échec du découpage du dataset: {str(e)}")
            raise
        
        # Étape 4: conteneurisation et création des tâches pour chaque shard
        tasks = []
        for i in range(num_shards):
            print(f"[INFO] Traitement du shard {i}...")
            shard_path = os.path.join(input_dir, f"shard_{i}")
            
            # Vérifier si le shard existe
            if not os.path.exists(shard_path):
                print(f"[WARNING] Le shard {i} n'existe pas, ignoré.")
                continue
                
            # Vérifier la taille du fichier de données
            data_path = os.path.join(shard_path, "data.pkl")
            if not os.path.exists(data_path):
                print(f"[WARNING] Le fichier de données pour le shard {i} n'existe pas, ignoré.")
                continue
                
            input_size = os.path.getsize(data_path) // (1024 * 1024)  # Convertir en Mo
            
            if (input_size > (min_resources["min_disk"] * 1024)):  # Convertir Go en Mo
                print(f"[WARNING] Shard {i} dépasse la limite de disque minimale. Ignoré.")
                continue
                
            # Génération d'un ID unique pour la tâche
            task_id = str(uuid.uuid4())
            
            # Créer l'image Docker pour cette tâche
            try:
                docker_img_name = containerize_task(
                    task_id, 
                    workflow_instance.workflow_type,
                    train_script,
                    base_path
                )
                
                # Extraire le nom et le tag du format complet
                docker_parts = docker_img_name.split('/')
                docker_img = {
                    "name": '/'.join(docker_parts[:-1]),
                    "tag": docker_parts[-1].split(':')[-1] if ':' in docker_parts[-1] else "latest"
                }
                
                print(f"[INFO] Image Docker créée: {docker_img_name}")
            except Exception as e:
                print(f"[ERROR] Échec de conteneurisation pour le shard {i}: {str(e)}")
                continue
            
            # Créer la tâche pour ce shard
            task = Task.objects.create(
                workflow=workflow_instance,
                name=f"ML Training Shard {i}",
                description=f"Entraînement sur le shard {i} du dataset",
                command="python /app/train_on_shard.py",
                parameters=[],
                input_files=[{
                    "container_path": f"/app/inputs/shard_{i}/data.pkl",
                    "host_path": os.path.join(input_dir, f"shard_{i}/data.pkl"),
                    "url": f"{manager_host}/api/files/inputs/shard_{i}/data.pkl"
                }],
                output_files=[f"/app/outputs/shard_{i}/model.pt"],
                status=TaskStatus.CREATED,
                parent_task=None,
                is_subtask=False,
                progress=0,
                created_at=timezone.now(),
                start_time=None,
                docker_info=docker_img,
                required_resources={
                    "cpu": min_resources["min_cpu"],
                    "ram": min_resources["min_ram"],
                    "disk": min_resources["min_disk"],
                },
                estimated_max_time=300,  # 5 minutes par défaut
                input_size=input_size
            )
            tasks.append(task)
            print(f"[INFO] Tâche créée pour le shard {i}: {task.id}")
            
        # Étape 5: mettre à jour le workflow
        if tasks:
            # Mise à jour du statut du workflow
            workflow_instance.status = WorkflowStatus.ASSIGNING
            workflow_instance.save()
            
            print(f"[INFO] Workflow mis à jour avec {len(tasks)} tâches.")
            return tasks
        else:
            print("[WARNING] Aucune tâche créée. Workflow échoué.")
            workflow_instance.status = WorkflowStatus.FAILED
            workflow_instance.save()
            return []
    except Exception as e:
        print(f"[ERROR] Échec du découpage du workflow: {str(e)}")
        workflow_instance.status = WorkflowStatus.FAILED
        workflow_instance.save()
        raise

def split_workflow(workflow_id):
    """
    Fonction principale pour découper un workflow selon son type.
    
    Args:
        workflow_id (uuid.UUID): ID du workflow à découper
    
    Returns:
        list: Liste des tâches créées
    """
    try:
        # Récupérer le workflow
        workflow_instance = Workflow.objects.get(id=workflow_id)
        
        # Mise à jour du statut
        workflow_instance.status = WorkflowStatus.SPLITTING
        workflow_instance.save()
        print(f"[INFO] Début du découpage du workflow {workflow_id} de type {workflow_instance.workflow_type}")
        
        # Déterminer le type de workflow et appeler la fonction appropriée
        if workflow_instance.workflow_type == WorkflowType.ML_TRAINING:
            # Chemin de base pour ce type de workflow
            base_path = os.path.join(settings.BASE_DIR, "workflows", "examples", "distributed_training_demo")
            
            # Appeler la fonction de découpage spécifique
            tasks = split_ml_training_workflow(workflow_instance, base_path)
            return tasks
        elif workflow_instance.workflow_type == WorkflowType.MATRIX_ADDITION:
            # Implémenter selon les besoins
            raise NotImplementedError("Découpage pour MATRIX_ADDITION non implémenté")
        elif workflow_instance.workflow_type == WorkflowType.MATRIX_MULTIPLICATION:
            # Implémenter selon les besoins
            raise NotImplementedError("Découpage pour MATRIX_MULTIPLICATION non implémenté")
        else:
            raise ValueError(f"Type de workflow non supporté: {workflow_instance.workflow_type}")
    except Exception as e:
        print(f"[ERROR] Échec du découpage du workflow {workflow_id}: {str(e)}")
        raise