import asyncio
import json
import logging
import threading
import traceback
import sys
from functools import wraps

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Ajouter un handler pour afficher les logs dans la console
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Liste des callbacks enregistrés par type d'événement
_callbacks = {}

def register_callback(event_type):
    """
    Décorateur pour enregistrer une fonction de callback pour un type d'événement.
    
    Usage:
        @register_callback('workflow_status_change')
        def handle_workflow_status_change(data):
            # Traitement de l'événement
    """
    def decorator(func):
        if event_type not in _callbacks:
            _callbacks[event_type] = []
            logger.info(f"Création d'une nouvelle liste de callbacks pour l'événement '{event_type}'")
        
        _callbacks[event_type].append(func)
        logger.info(f"Callback '{func.__name__}' enregistré pour l'événement '{event_type}'")
        logger.debug(f"Callbacks enregistrés pour '{event_type}': {[cb.__name__ for cb in _callbacks[event_type]]}")
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Exécution du callback '{func.__name__}' pour l'événement '{event_type}'")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def notify_event(event_type, data):
    """
    Notifie tous les callbacks enregistrés pour un type d'événement.
    
    Args:
        event_type: Type d'événement
        data: Données associées à l'événement
    """
    logger.info(f"Notification d'événement '{event_type}' reçue avec les données: {data}")
    
    if event_type in _callbacks:
        callback_count = len(_callbacks[event_type])
        logger.info(f"Exécution de {callback_count} callbacks pour l'événement '{event_type}'")
        
        for i, callback in enumerate(_callbacks[event_type]):
            try:
                logger.debug(f"Exécution du callback {i+1}/{callback_count} '{callback.__name__}' pour '{event_type}'")
                callback(data)
                logger.debug(f"Callback '{callback.__name__}' exécuté avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution du callback '{callback.__name__}' pour '{event_type}': {e}")
                logger.error(traceback.format_exc())
    else:
        logger.warning(f"Aucun callback enregistré pour l'événement '{event_type}'")
        logger.debug(f"Callbacks disponibles: {list(_callbacks.keys())}")
        logger.debug(f"Données de l'événement ignorées: {data}")


# Enregistrement des callbacks pour les événements de workflow
@register_callback('workflow_status_change')
def handle_workflow_status_change(data):
    """
    Gère les changements de statut des workflows.
    
    Args:
        data: Données du changement de statut
    """
    from .server import get_ws_server
    
    workflow_id = data.get('workflow_id')
    if workflow_id:
        # Créer une tâche asynchrone pour notifier les clients
        async def notify():
            server = get_ws_server()
            await server.notify_workflow_update(workflow_id, data)
        
        # Exécuter la tâche dans une nouvelle boucle asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(notify())
        finally:
            loop.close()

@register_callback('workflow_submission')
def handle_workflow_submission(data):
    """
    Gère les événements de soumission de workflow.
    
    Args:
        data: Données de soumission du workflow
    """
    from .server import get_ws_server
    
    workflow_id = data.get('workflow_id')
    if workflow_id:
        # Créer une tâche asynchrone pour notifier les clients
        async def notify():
            server = get_ws_server()
            await server.notify_workflow_update(workflow_id, {
                'type': 'workflow_update',
                'workflow_id': workflow_id,
                'status': 'SUBMITTED',
                'message': 'Workflow soumis avec succès'
            })
        
        # Exécuter la tâche dans une nouvelle boucle asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(notify())
        finally:
            loop.close()

@register_callback('workflow_error')
def handle_workflow_error(data):
    """
    Gère les erreurs liées aux workflows.
    
    Args:
        data: Données d'erreur
    """
    from .server import get_ws_server
    
    workflow_id = data.get('workflow_id')
    if workflow_id:
        # Créer une tâche asynchrone pour notifier les clients
        async def notify():
            server = get_ws_server()
            await server.notify_workflow_update(workflow_id, {
                'type': 'workflow_update',
                'workflow_id': workflow_id,
                'status': 'ERROR',
                'message': data.get('message', 'Une erreur est survenue')
            })
        
        # Exécuter la tâche dans une nouvelle boucle asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(notify())
        finally:
            loop.close()

@register_callback('workflow_update')
def handle_workflow_update(data):
    """
    Gère les mises à jour des workflows.
    
    Args:
        data: Données du changement de statut
    """
    from .server import get_ws_server
    
    workflow_id = data.get('workflow_id')
    if workflow_id:
        # Créer une tâche asynchrone pour notifier les clients
        async def notify():
            server = get_ws_server()
            await server.notify_workflow_update(workflow_id, data)
        
        # Exécuter la tâche dans une nouvelle boucle asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(notify())
        finally:
            loop.close()

# Fonction pour démarrer le serveur WebSocket dans un thread séparé
def start_websocket_server():
    """
    Démarre le serveur WebSocket dans un thread séparé.
    """
    from .server import get_ws_server
    
    def run_server():
        server = get_ws_server()
        server.start_server()
    
    # Démarrer le serveur dans un thread
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info("Serveur WebSocket démarré dans un thread séparé")
    return thread
