"""
Serveur de fichiers simple pour servir les fichiers d'entrée aux volontaires.
"""

import os
import threading
import logging
import http.server
import socketserver
from typing import Optional
from workflows.models import Workflow

logger = logging.getLogger(__name__)

# Dictionnaire pour stocker les serveurs en cours d'exécution par workflow
active_servers = {}

class WorkflowFileHandler(http.server.SimpleHTTPRequestHandler):
    """Gestionnaire HTTP personnalisé pour servir les fichiers d'un workflow."""
    
    def __init__(self, *args, workflow_base_dir=None, **kwargs):
        self.workflow_base_dir = workflow_base_dir
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Traduit le chemin de l'URL en chemin de fichier local."""
        # Supprimer les paramètres de requête s'il y en a
        if '?' in path:
            path = path.split('?', 1)[0]
        
        # Supprimer les fragments s'il y en a
        if '#' in path:
            path = path.split('#', 1)[0]
        
        # Normaliser le chemin
        path = path.split('?', 1)[0]
        path = path.split('/', 1)[1] if path.startswith('/') else path
        
        # Construire le chemin complet
        return os.path.join(self.workflow_base_dir, path)
    
    def log_message(self, format, *args):
        """Rediriger les logs vers le logger de l'application."""
        logger.info(f"FileServer: {format % args}")

def start_file_server(workflow: Workflow, port: int = 0) -> int:
    """
    Démarre un serveur de fichiers pour un workflow spécifique.
    
    Args:
        workflow: L'instance du workflow
        port: Port sur lequel démarrer le serveur (0 = port aléatoire)
        
    Returns:
        Le port sur lequel le serveur a été démarré
    """
    workflow_id = str(workflow.id)
    
    # Vérifier si un serveur est déjà en cours pour ce workflow
    if workflow_id in active_servers:
        logger.info(f"Un serveur de fichiers est déjà en cours pour le workflow {workflow_id}")
        return active_servers[workflow_id]['port']
    
    # Déterminer le répertoire de base pour les fichiers du workflow
    workflow_base_dir = workflow.input_path
    
    if not os.path.exists(workflow_base_dir):
        os.makedirs(workflow_base_dir)
        logger.warning(f"Le répertoire du workflow {workflow_id} n'existe pas, il a été créé: {workflow_base_dir}")
    
    # Créer un gestionnaire de requêtes avec le répertoire de base du workflow
    handler = lambda *args, **kwargs: WorkflowFileHandler(*args, workflow_base_dir=workflow_base_dir, **kwargs)
    
    # Créer et démarrer le serveur
    httpd = socketserver.ThreadingTCPServer(("", port), handler)
    server_port = httpd.server_address[1]
    
    # Démarrer le serveur dans un thread séparé
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Enregistrer le serveur actif
    active_servers[workflow_id] = {
        'server': httpd,
        'thread': server_thread,
        'port': server_port
    }
    
    logger.info(f"Serveur de fichiers démarré pour le workflow {workflow_id} sur le port {server_port}")
    return server_port

def stop_file_server(workflow_id: str) -> bool:
    """
    Arrête le serveur de fichiers pour un workflow spécifique.
    
    Args:
        workflow_id: ID du workflow
        
    Returns:
        True si le serveur a été arrêté, False sinon
    """
    if workflow_id not in active_servers:
        logger.warning(f"Aucun serveur de fichiers en cours pour le workflow {workflow_id}")
        return False
    
    # Arrêter le serveur
    try:
        active_servers[workflow_id]['server'].shutdown()
        active_servers[workflow_id]['server'].server_close()
        del active_servers[workflow_id]
        logger.info(f"Serveur de fichiers arrêté pour le workflow {workflow_id}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du serveur de fichiers pour le workflow {workflow_id}: {e}")
        return False
