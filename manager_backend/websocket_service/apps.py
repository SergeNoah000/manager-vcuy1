from django.apps import AppConfig
import logging
import sys
import traceback

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

class WebsocketServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'websocket_service'

    def ready(self):
        """Démarrage du serveur WebSocket lors du démarrage de l'application."""
        # Éviter de démarrer le serveur lors des appels de manage.py
        import sys
        logger.debug(f"Arguments de la commande: {sys.argv}")
        
        if 'runserver' in sys.argv:
            try:
                logger.info("Initialisation du démarrage du serveur WebSocket...")
                from .client import start_websocket_server
                
                logger.info("Appel de la fonction start_websocket_server()")
                self.websocket_thread = start_websocket_server()
                logger.info("Serveur WebSocket démarré avec succès dans un thread séparé")
            except Exception as e:
                logger.error(f"Erreur lors du démarrage du serveur WebSocket: {e}")
                logger.error(traceback.format_exc())
        else:
            logger.info("Commande non-runserver détectée, le serveur WebSocket ne sera pas démarré")
            logger.debug(f"Commande actuelle: {' '.join(sys.argv)}")
