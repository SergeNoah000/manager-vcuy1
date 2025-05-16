# manager_backend/workflows/utils/docker_manager.py
import os
import subprocess
import logging
import tempfile
import shutil
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)

class DockerManager:
    """
    Gestionnaire pour les opérations Docker:
    - Construction d'images
    - Push vers le registry
    - Téléchargement d'images
    """
    
    def __init__(self):
        self.registry = settings.DOCKER_REGISTRY
        self.namespace = settings.DOCKER_NAMESPACE
        self.push_enabled = settings.DOCKER_PUSH_ENABLED
        self.username = settings.DOCKER_USERNAME
        self.password = settings.DOCKER_PASSWORD
        
        # Timeout pour les opérations (en secondes)
        self.build_timeout = settings.DOCKER_BUILD_TIMEOUT
        self.push_timeout = settings.DOCKER_PUSH_TIMEOUT
        self.pull_timeout = settings.DOCKER_PULL_TIMEOUT
    
    def login(self):
        """Se connecte au registry Docker"""
        try:
            cmd = ["docker", "login", self.registry, "-u", self.username, "-p", self.password]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Échec de connexion à Docker: {result.stderr}")
                return False
            
            logger.info(f"Connexion réussie à {self.registry}")
            return True
        except Exception as e:
            logger.exception(f"Erreur lors de la connexion à Docker: {str(e)}")
            return False
    
    def build_image(self, dockerfile_path, context_path, image_name, tag="latest"):
        """
        Construit une image Docker à partir d'un Dockerfile.
        
        Args:
            dockerfile_path (str): Chemin vers le Dockerfile
            context_path (str): Chemin vers le contexte de build
            image_name (str): Nom de l'image
            tag (str, optional): Tag de l'image. Par défaut à "latest".
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            full_image_name = f"{self.registry}/{self.namespace}/{image_name}:{tag}"
            
            cmd = [
                "docker", "build",
                "-f", dockerfile_path,
                "-t", full_image_name,
                context_path
            ]
            
            logger.info(f"Construction de l'image Docker: {full_image_name}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.build_timeout)
            
            if result.returncode != 0:
                logger.error(f"Échec de construction de l'image Docker: {result.stderr}")
                return False, result.stderr
            
            logger.info(f"Image Docker construite avec succès: {full_image_name}")
            return True, full_image_name
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de la construction de l'image Docker")
            return False, "Timeout lors de la construction de l'image Docker"
        except Exception as e:
            logger.exception(f"Erreur lors de la construction de l'image Docker: {str(e)}")
            return False, str(e)
    
    def push_image(self, image_name, tag="latest"):
        """
        Pousse une image vers le registry Docker.
        
        Args:
            image_name (str): Nom de l'image (sans le registry/namespace)
            tag (str, optional): Tag de l'image. Par défaut à "latest".
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        if not self.push_enabled:
            logger.info("Push Docker désactivé dans les paramètres")
            return True, "Push Docker désactivé"
        
        try:
            # Se connecter d'abord
            if not self.login():
                return False, "Échec de connexion au registry Docker"
            
            full_image_name = f"{self.registry}/{self.namespace}/{image_name}:{tag}"
            
            cmd = ["docker", "push", full_image_name]
            
            logger.info(f"Push de l'image Docker: {full_image_name}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.push_timeout)
            
            if result.returncode != 0:
                logger.error(f"Échec de push de l'image Docker: {result.stderr}")
                return False, result.stderr
            
            logger.info(f"Image Docker poussée avec succès: {full_image_name}")
            return True, full_image_name
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors du push de l'image Docker")
            return False, "Timeout lors du push de l'image Docker"
        except Exception as e:
            logger.exception(f"Erreur lors du push de l'image Docker: {str(e)}")
            return False, str(e)
    
    def prepare_dockerfile_for_task(self, task_id, base_image="python:3.10-slim", script_path=None, input_files=None, output_files=None):
        """
        Prépare un Dockerfile personnalisé pour une tâche spécifique.
        
        Args:
            task_id (str): ID de la tâche
            base_image (str): Image de base à utiliser
            script_path (str): Chemin vers le script principal à exécuter
            input_files (list): Liste des fichiers d'entrée à copier
            output_files (list): Liste des fichiers de sortie à créer
            
        Returns:
            tuple: (success, dockerfile_path, context_path)
        """
        try:
            # Créer un répertoire temporaire pour le contexte Docker
            context_path = tempfile.mkdtemp(prefix=f"docker_context_{task_id}_")
            
            # Créer le Dockerfile
            dockerfile_path = os.path.join(context_path, "Dockerfile")
            
            # Contenu du Dockerfile
            dockerfile_content = [
                f"FROM {base_image}",
                "WORKDIR /app",
            ]
            
            # Copier les fichiers nécessaires
            if script_path:
                # Copier le script dans le contexte
                script_name = os.path.basename(script_path)
                dest_script_path = os.path.join(context_path, script_name)
                shutil.copy2(script_path, dest_script_path)
                
                # Ajouter au Dockerfile
                dockerfile_content.append(f"COPY {script_name} /app/")
            
            # Créer les répertoires pour les entrées/sorties
            dockerfile_content.extend([
                "RUN mkdir -p /app/inputs",
                "RUN mkdir -p /app/outputs",
                "VOLUME /app/inputs",
                "VOLUME /app/outputs",
            ])
            
            # Installer les dépendances
            dockerfile_content.append("RUN pip install torch torchvision")
            
            # Définir l'entrée
            if script_path:
                dockerfile_content.append(f"ENTRYPOINT [\"python\", \"/app/{script_name}\"]")
            
            # Écrire le Dockerfile
            with open(dockerfile_path, "w") as f:
                f.write("\n".join(dockerfile_content))
            
            logger.info(f"Dockerfile créé avec succès dans {dockerfile_path}")
            return True, dockerfile_path, context_path
        except Exception as e:
            logger.exception(f"Erreur lors de la préparation du Dockerfile: {str(e)}")
            return False, None, None
    
    def build_and_push_task_image(self, task_id, script_path, base_image="python:3.10-slim"):
        """
        Construit et pousse une image Docker pour une tâche spécifique.
        
        Args:
            task_id (str): ID de la tâche
            script_path (str): Chemin vers le script principal à exécuter
            base_image (str): Image de base à utiliser
            
        Returns:
            tuple: (success, image_name)
        """
        try:
            # Préparer le Dockerfile
            success, dockerfile_path, context_path = self.prepare_dockerfile_for_task(
                task_id, base_image, script_path
            )
            
            if not success:
                return False, "Échec de préparation du Dockerfile"
            
            # Générer un nom d'image unique
            image_name = f"task-{task_id}-{uuid.uuid4().hex[:8]}"
            
            # Construire l'image
            build_success, build_result = self.build_image(
                dockerfile_path, context_path, image_name
            )
            
            # Nettoyer le contexte temporaire
            try:
                shutil.rmtree(context_path)
            except Exception as e:
                logger.warning(f"Erreur lors du nettoyage du contexte Docker: {str(e)}")
            
            if not build_success:
                return False, build_result
            
            # Pousser l'image si nécessaire
            if self.push_enabled:
                push_success, push_result = self.push_image(image_name)
                if not push_success:
                    return False, push_result
            
            # Format: registry/namespace/image:tag
            full_image_name = f"{self.registry}/{self.namespace}/{image_name}:latest"
            return True, full_image_name
        except Exception as e:
            logger.exception(f"Erreur lors de la construction et du push de l'image: {str(e)}")
            return False, str(e)

# Fonction utilitaire pour obtenir une instance du gestionnaire Docker
def get_docker_manager():
    return DockerManager()