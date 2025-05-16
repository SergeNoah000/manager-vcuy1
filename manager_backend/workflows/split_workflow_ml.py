# manager_backend/workflows/split_workflow_ml.py
import os
import uuid
import sys
import json
import pickle
import subprocess 
import shutil      
from django.utils import timezone
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
    Crée et pousse un conteneur Docker pour une tâche spécifique.
    Si Docker n'est pas disponible, simule la conteneurisation.
    
    Args:
        task_id (str): ID de la tâche
        workflow_type (str): Type de workflow
        script_path (str): Chemin vers le script principal
        base_path (str): Chemin de base pour les scripts et données
        
    Returns:
        dict: Informations de l'image Docker (nom et tag)
    """
    print(f"[INFO] Début de conteneurisation pour la tâche {task_id}")
    
    # Mode simulation par défaut (permet de créer des tâches même sans Docker)
    simulate_docker = True
    
    try:
        # Vérifier que Docker est installé, sinon passer en mode simulation
        try:
            # Utiliser le module 'subprocess' importé au niveau global
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                check=False  # Ne pas échouer si Docker n'est pas trouvé
            )
            if result.returncode == 0:
                print(f"[INFO] Docker installé: {result.stdout.strip()}")
                simulate_docker = False  # Docker est disponible
            else:
                print(f"[WARNING] Docker non trouvé: {result.stderr}")
                simulate_docker = True  # Passer en mode simulation
        except Exception as e:
            print(f"[WARNING] Erreur lors de la vérification de Docker: {str(e)}")
            simulate_docker = True  # Passer en mode simulation
        
        # Mode simulation Docker (pour environnements sans Docker)
        if simulate_docker:
            # Générer un nom d'image simulé
            image_name = f"simu-task-{task_id[:8]}"
            registry = "docker.io"
            namespace = "patricehub"
            tag = "latest"
            full_image_name = f"{registry}/{namespace}/{image_name}:{tag}"
            
            print(f"[INFO] Simulation Docker: {full_image_name}")
            
            # Retourner les informations Docker simulées
            docker_info = {
                "registry": registry,
                "namespace": namespace,
                "name": image_name,
                "tag": tag,
                "full_name": full_image_name,
                "simulated": True
            }
            
            print(f"[INFO] Conteneurisation simulée terminée pour la tâche {task_id}")
            return docker_info
        
        # Mode réel Docker (uniquement si Docker est disponible)
        try:
            # Obtenir le gestionnaire Docker
            docker_manager = get_docker_manager()
            
            # Déterminer l'image de base
            base_image = "alpine:latest"
            print(f"[INFO] Utilisation de l'image de base {base_image}")
            
            # 1. Préparation du Dockerfile et du contexte
            success, dockerfile_path, context_path = docker_manager.prepare_dockerfile_for_task(
                task_id, base_image, script_path
            )
            
            if not success:
                raise Exception(f"Échec de préparation du Dockerfile pour la tâche {task_id}")
            
            # 2. Construction de l'image
            task_prefix = f"task-{task_id[:8]}"
            image_name = f"{task_prefix}-{uuid.uuid4().hex[:8]}"
            
            build_success, build_result = docker_manager.build_image(
                dockerfile_path, context_path, image_name
            )
            
            # Nettoyer le contexte temporaire
            try:
                shutil.rmtree(context_path)
            except Exception as e:
                print(f"[WARNING] Erreur lors du nettoyage: {str(e)}")
            
            if not build_success:
                raise Exception(f"Échec de construction de l'image: {build_result}")
            
            # 3. Push de l'image vers Docker Hub
            if docker_manager.push_enabled:
                push_success, push_result = docker_manager.push_image(image_name)
                if not push_success:
                    raise Exception(f"Échec de push de l'image: {push_result}")
            
            # 4. Préparer les informations Docker
            registry = docker_manager.registry
            namespace = docker_manager.namespace
            tag = "latest"
            full_image_name = f"{registry}/{namespace}/{image_name}:{tag}"
            
            # 5. Retourner les informations complètes
            docker_info = {
                "registry": registry,
                "namespace": namespace,
                "name": image_name,
                "tag": tag,
                "full_name": full_image_name,
                "simulated": False
            }
            
            print(f"[INFO] Conteneurisation réelle terminée: {full_image_name}")
            return docker_info
            
        except Exception as e:
            print(f"[ERROR] Échec de conteneurisation Docker réelle: {str(e)}")
            # En cas d'échec, passer au mode simulation
            print(f"[INFO] Recours au mode simulation suite à l'échec Docker")
            
            # Créer une image simulée (code direct, pas d'appel récursif)
            image_name = f"simu-task-{task_id[:8]}"
            registry = "docker.io"
            namespace = "patricehub"
            tag = "latest"
            full_image_name = f"{registry}/{namespace}/{image_name}:{tag}"
            
            docker_info = {
                "registry": registry,
                "namespace": namespace,
                "name": image_name,
                "tag": tag,
                "full_name": full_image_name,
                "simulated": True,
                "error": str(e)
            }
            
            print(f"[INFO] Conteneurisation simulée créée après échec Docker")
            return docker_info
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la conteneurisation: {str(e)}")
        # En dernier recours, fournir une image simulée de secours
        fallback_image_name = f"fallback-{task_id[:8]}"
        fallback_info = {
            "registry": "docker.io",
            "namespace": "patricehub",
            "name": fallback_image_name,
            "tag": "latest",
            "full_name": f"docker.io/patricehub/fallback-{task_id[:8]}:latest",
            "simulated": True,
            "fallback": True
        }
        print(f"[INFO] Image de secours créée: {fallback_info['full_name']}")
        return fallback_info

def generate_default_scripts(base_path):
    """
    Crée les scripts par défaut s'ils n'existent pas.
    
    Args:
        base_path (str): Chemin du répertoire de base
    """
    split_script_path = os.path.join(base_path, "split_dataset.py")
    train_script_path = os.path.join(base_path, "train_on_shard.py")
    
    # Créer le script de division s'il n'existe pas
    if not os.path.exists(split_script_path):
        print(f"[INFO] Création du script de division manquant: {split_script_path}")
        split_script_content = """
import os
import pickle
import numpy as np
import sys
from torchvision.datasets import CIFAR10
from torchvision import transforms
import shutil
import argparse

def download_cifar10():
    \"\"\"Télécharge le dataset CIFAR10 s'il n'est pas déjà présent\"\"\"
    print(f"[INFO] Téléchargement du dataset CIFAR10...")
    # Le téléchargement se fait automatiquement lors de la première utilisation
    CIFAR10('./data', train=True, download=True, transform=transforms.ToTensor())
    print(f"[INFO] Dataset téléchargé avec succès!")

def split_dataset(num_shards):
    \"\"\"
    Divise le dataset CIFAR10 en num_shards parties égales.
    Chaque shard est sauvegardé dans un répertoire distinct.
    
    Args:
        num_shards (int): Nombre de shards à créer
    \"\"\"
    print(f"[INFO] Découpage du dataset en {num_shards} shards...")
    
    # Assurer que les répertoires existent
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "inputs")
    output_dir = os.path.join(base_dir, "outputs")
    
    # Créer les répertoires s'ils n'existent pas
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Charger le dataset CIFAR10
        cifar10 = CIFAR10('./data', train=True, download=False, transform=transforms.ToTensor())
        data = cifar10.data  # numpy array de shape (50000, 32, 32, 3)
        targets = np.array(cifar10.targets)  # liste de 50000 labels
    except Exception as e:
        print(f"[WARNING] Erreur lors du chargement du dataset: {str(e)}")
        # Créer des données factices pour permettre le fonctionnement du processus
        print("[INFO] Création de données factices pour le test")
        data = np.random.randint(0, 255, (1000, 32, 32, 3), dtype=np.uint8)
        targets = np.random.randint(0, 10, 1000)
    
    # Calculer la taille de chaque shard
    samples_per_shard = len(data) // num_shards
    
    # Diviser les données en shards
    for i in range(num_shards):
        # Calculer les indices de début et fin pour ce shard
        start_idx = i * samples_per_shard
        end_idx = (i + 1) * samples_per_shard if i < num_shards - 1 else len(data)
        
        # Extraire les données et cibles pour ce shard
        shard_data = data[start_idx:end_idx]
        shard_targets = targets[start_idx:end_idx]
        
        # Créer un répertoire pour ce shard
        shard_dir = os.path.join(input_dir, f"shard_{i}")
        os.makedirs(shard_dir, exist_ok=True)
        
        # Créer aussi un répertoire de sortie pour ce shard
        shard_output_dir = os.path.join(output_dir, f"shard_{i}")
        os.makedirs(shard_output_dir, exist_ok=True)
        
        # Sauvegarder les données et cibles dans ce répertoire
        with open(os.path.join(shard_dir, "data.pkl"), "wb") as f:
            pickle.dump((shard_data, shard_targets), f)
        
        print(f"[INFO] Shard {i}: {len(shard_data)} échantillons sauvegardés.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Découpe le dataset CIFAR10 en N shards.")
    parser.add_argument("num_shards", type=int, help="Nombre de shards à créer")
    args = parser.parse_args()
    
    # Télécharger le dataset si nécessaire
    try:
        download_cifar10()
    except Exception as e:
        print(f"[WARNING] Échec du téléchargement: {str(e)}")
    
    # Découper le dataset
    split_dataset(args.num_shards)
    
    print("[INFO] Découpage terminé avec succès!")
"""
        with open(split_script_path, "w") as f:
            f.write(split_script_content)
    
    # Créer le script d'entraînement s'il n'existe pas
    if not os.path.exists(train_script_path):
        print(f"[INFO] Création du script d'entraînement manquant: {train_script_path}")
        train_script_content = """
import os
import pickle
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32*32*3, 128), nn.ReLU(),
            nn.Linear(128, 10)
        )
    
    def forward(self, x):
        return self.fc(x)

def load_shard():
    \"\"\"Charge le shard de données qui est monté dans le conteneur\"\"\"
    input_path = "/app/inputs/shard_0/data.pkl"  # Le path sera remplacé dynamiquement
    
    # Vérifier si le fichier existe
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Le fichier {input_path} n'existe pas.")
    
    # Charger les données
    with open(input_path, "rb") as f:
        data, targets = pickle.load(f)
    
    # Convertir en tenseurs PyTorch
    X = torch.tensor(data, dtype=torch.float32) / 255.0  # Normalisation
    X = X.permute(0, 3, 1, 2)  # Changer l'ordre des dimensions pour PyTorch
    y = torch.tensor(targets, dtype=torch.long)
    
    return X, y

def train_model(X, y, epochs=5, batch_size=64):
    \"\"\"Entraîne un modèle sur les données fournies\"\"\"
    # Créer le dataset et dataloader
    dataset = TensorDataset(X, y)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialiser le modèle
    model = SimpleNet()
    
    # Définir la perte et l'optimiseur
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Entraînement
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    print(f"Entraînement sur {len(X)} échantillons pour {epochs} époques...")
    
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0
        
        for batch_X, batch_y in dataloader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            # Réinitialiser les gradients
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            # Backward pass et optimisation
            loss.backward()
            optimizer.step()
            
            # Statistiques
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
        
        epoch_loss = running_loss / len(dataloader)
        epoch_acc = 100 * correct / total
        print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.2f}%")
    
    print("Entraînement terminé!")
    
    # Retourner le dictionnaire d'état du modèle
    return model.state_dict()

def save_model(model_state):
    \"\"\"Sauvegarde le modèle entraîné\"\"\"
    output_dir = "/app/outputs/shard_0"  # Le path sera remplacé dynamiquement
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "model.pt")
    torch.save(model_state, output_path)
    print(f"Modèle sauvegardé dans {output_path}")

if __name__ == "__main__":
    try:
        # Charger les données
        X, y = load_shard()
        print(f"Données chargées: {X.shape}, {y.shape}")
        
        # Entraîner le modèle
        model_state = train_model(X, y)
        
        # Sauvegarder le modèle
        save_model(model_state)
        
        print("Entraînement et sauvegarde terminés avec succès!")
    except Exception as e:
        print(f"[ERROR] Une erreur s'est produite: {str(e)}")
        raise
"""
        with open(train_script_path, "w") as f:
            f.write(train_script_content)
    
    print(f"[INFO] Scripts vérifiés et créés si nécessaire")

def split_ml_training_workflow(workflow_instance, base_path):
    """
    Effectue le découpage pour un workflow ML_TRAINING à partir du script externe.
    Cette fonction est robuste et continue même en cas d'erreurs.
    """
    print(f"[INFO] Début du processus de découpage pour le workflow {workflow_instance.id}")
    created_tasks = []
    
    try:
        # Générer les scripts s'ils n'existent pas
        generate_default_scripts(base_path)
        
        # 1. Préparation des répertoires
        dataset_path = os.path.join(base_path, "data")
        input_dir = os.path.join(base_path, "inputs")
        output_dir = os.path.join(base_path, "outputs")
        split_script = os.path.join(base_path, "split_dataset.py")
        train_script = os.path.join(base_path, "train_on_shard.py")
        
        os.makedirs(dataset_path, exist_ok=True)
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # 2. Déterminer les ressources minimales
        min_resources = get_min_volunteer_resources()
        print(f"[INFO] Ressources minimales: {min_resources}")
        
        # 3. Diviser le dataset
        num_shards = 3  # Valeur par défaut
        try:
            # Vérifier les scripts
            if not os.path.exists(split_script) or not os.path.exists(train_script):
                raise FileNotFoundError("Scripts nécessaires manquants")
                
            # Exécuter le script de division avec timeout et capture de sortie
            print(f"[INFO] Exécution du script de division: {split_script}")
            
            try:
                # Lancer le script de découpage avec timeout de 5 minutes
                process = subprocess.run(
                    [sys.executable, split_script, str(num_shards)],
                    check=True,
                    cwd=base_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                # Afficher la sortie du script
                if process.stdout:
                    for line in process.stdout.splitlines():
                        print(f"[SPLIT] {line}")
                
                print(f"[INFO] Découpage terminé avec succès. {num_shards} shards créés.")
            except subprocess.TimeoutExpired:
                print("[WARNING] Timeout lors de l'exécution du script de découpage")
                # Continuer avec les shards existants
            except Exception as e:
                print(f"[WARNING] Erreur lors de l'exécution du script de découpage: {str(e)}")
                # Continuer avec les shards existants
                
        except Exception as e:
            print(f"[WARNING] Échec du découpage du dataset: {str(e)}")
            # Ne pas relancer l'exception, créer des shards factices
            print("[INFO] Création de shards factices pour permettre le test")
            for i in range(3):
                shard_dir = os.path.join(input_dir, f"shard_{i}")
                os.makedirs(shard_dir, exist_ok=True)
                
                # Créer un fichier de données factice
                with open(os.path.join(shard_dir, "data.pkl"), "wb") as f:
                    # Données factices simples
                    data = np.random.randint(0, 255, (100, 32, 32, 3), dtype=np.uint8)
                    targets = np.random.randint(0, 10, 100)
                    pickle.dump((data, targets), f)
            
            print("[INFO] Shards factices créés avec succès")
        
        # 4. Trouver les shards disponibles
        available_shards = []
        try:
            for item in os.listdir(input_dir):
                shard_path = os.path.join(input_dir, item)
                if os.path.isdir(shard_path) and os.path.exists(os.path.join(shard_path, "data.pkl")):
                    available_shards.append(item)
            
            if not available_shards:
                print("[WARNING] Aucun shard trouvé!")
        except Exception as e:
            print(f"[WARNING] Erreur lors de la recherche de shards: {str(e)}")
        
        # 5. Créer des tâches pour chaque shard
        for shard_name in available_shards:
            try:
                # Extraire l'indice du shard
                shard_idx = int(shard_name.split("_")[1])
                print(f"[INFO] Traitement du shard {shard_idx}...")
            except (IndexError, ValueError):
                shard_idx = len(created_tasks)
                print(f"[INFO] Traitement du shard avec index dérivé {shard_idx}...")
            
            shard_path = os.path.join(input_dir, shard_name)
            data_path = os.path.join(shard_path, "data.pkl")
            
            # Vérifier la taille du fichier
            try:
                input_size = os.path.getsize(data_path) // (1024 * 1024)  # Convertir en Mo
            except Exception as e:
                print(f"[WARNING] Impossible de déterminer la taille du fichier: {str(e)}")
                input_size = 10  # Valeur par défaut en Mo
            
            # Vérifier les limites de ressources
            if input_size > (min_resources["min_disk"] * 1024):
                print(f"[WARNING] Shard {shard_idx} trop grand pour les ressources disponibles")
                continue
            
            # Générer un ID pour la tâche
            task_id = str(uuid.uuid4())
            
            # Créer ou simuler l'image Docker
            try:
                docker_info = containerize_task(
                    task_id, 
                    workflow_instance.workflow_type,
                    train_script,
                    base_path
                )
            except Exception as e:
                print(f"[WARNING] Échec de la conteneurisation: {str(e)}")
                # Utiliser une image Docker factice
                docker_info = {
                    "registry": "docker.io",
                    "namespace": "patricehub", 
                    "name": f"fallback-{task_id[:8]}",
                    "tag": "latest",
                    "full_name": f"docker.io/patricehub/fallback-{task_id[:8]}:latest",
                    "simulated": True
                }
            
            # Créer la tâche dans la base de données
            try:
                task = Task.objects.create(
                    workflow=workflow_instance,
                    name=f"ML Training Shard {shard_idx}",
                    description=f"Entraînement sur le shard {shard_idx} du dataset",
                    command="python /app/train_on_shard.py",
                    parameters=[],
                    input_files=[{
                        "container_path": f"/app/inputs/{shard_name}/data.pkl",
                        "host_path": os.path.join(input_dir, f"{shard_name}/data.pkl"),
                        "url": f"{manager_host}/api/files/inputs/{shard_name}/data.pkl"
                    }],
                    output_files=[f"/app/outputs/{shard_name}/model.pt"],
                    status=TaskStatus.CREATED,
                    parent_task=None,
                    is_subtask=False,
                    progress=0,
                    created_at=timezone.now(),
                    start_time=None,
                    docker_info=docker_info,
                    required_resources={
                        "cpu": min_resources["min_cpu"],
                        "ram": min_resources["min_ram"],
                        "disk": min_resources["min_disk"],
                    },
                    estimated_max_time=300,
                    input_size=input_size
                )
                created_tasks.append(task)
                print(f"[INFO] Tâche créée pour le shard {shard_idx}: {task.id}")
            except Exception as e:
                print(f"[ERROR] Échec de création de la tâche: {str(e)}")
                continue
        
        # 6. Mettre à jour le statut du workflow
        if created_tasks:
            workflow_instance.status = WorkflowStatus.ASSIGNING
            workflow_instance.save()
            print(f"[INFO] Workflow mis à jour avec {len(created_tasks)} tâches")
            return created_tasks
        else:
            workflow_instance.status = WorkflowStatus.FAILED
            workflow_instance.save()
            print("[WARNING] Aucune tâche créée, workflow marqué comme échoué")
            return []
            
    except Exception as e:
        import traceback
        print(f"[ERROR] Échec du découpage du workflow: {str(e)}")
        print(traceback.format_exc())
        workflow_instance.status = WorkflowStatus.FAILED
        workflow_instance.save()
        return created_tasks

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
            # Pour le développement, utiliser la même fonction que ML_TRAINING
            base_path = os.path.join(settings.BASE_DIR, "workflows", "examples", "distributed_training_demo")
            tasks = split_ml_training_workflow(workflow_instance, base_path)
            return tasks
        elif workflow_instance.workflow_type == WorkflowType.MATRIX_MULTIPLICATION:
            # Pour le développement, utiliser la même fonction que ML_TRAINING
            base_path = os.path.join(settings.BASE_DIR, "workflows", "examples", "distributed_training_demo")
            tasks = split_ml_training_workflow(workflow_instance, base_path)
            return tasks
        else:
            raise ValueError(f"Type de workflow non supporté: {workflow_instance.workflow_type}")
    except Exception as e:
        import traceback
        print(f"[ERROR] Échec du découpage du workflow {workflow_id}: {str(e)}")
        print(traceback.format_exc())
        return []