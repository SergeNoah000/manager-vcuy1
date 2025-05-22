import asyncio
import json
import logging
import websockets
import traceback
import sys
from uuid import uuid4

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

class WebSocketServer:
    """
    Serveur WebSocket simple pour la communication en temps réel avec le frontend.
    """
    def __init__(self, host='127.0.0.1', port=8765):
        self.host = host
        self.port = port
        self.clients = {}  # {client_id: websocket}
        self.workflow_subscriptions = {}  # {workflow_id: [client_id1, client_id2, ...]}
        self.server = None
        
    async def register(self, websocket):
        """Enregistre un nouveau client WebSocket."""
        client_id = str(uuid4())
        self.clients[client_id] = websocket
        logger.info(f"Client {client_id} connecté")
        return client_id
        
    async def unregister(self, client_id):
        """Désenregistre un client WebSocket."""
        if client_id in self.clients:
            del self.clients[client_id]
            
            # Supprimer les abonnements de ce client
            for workflow_id, clients in list(self.workflow_subscriptions.items()):
                if client_id in clients:
                    clients.remove(client_id)
                    if not clients:
                        del self.workflow_subscriptions[workflow_id]
                        
            logger.info(f"Client {client_id} déconnecté")
    
    async def subscribe_to_workflow(self, client_id, workflow_id):
        """Abonne un client à un workflow spécifique."""
        if workflow_id not in self.workflow_subscriptions:
            self.workflow_subscriptions[workflow_id] = []
        
        if client_id not in self.workflow_subscriptions[workflow_id]:
            self.workflow_subscriptions[workflow_id].append(client_id)
            logger.info(f"Client {client_id} abonné au workflow {workflow_id}")
    
    async def notify_workflow_update(self, workflow_id, data):
        """Notifie tous les clients abonnés à un workflow spécifique."""
        logger.info(f"Tentative de notification pour le workflow {workflow_id}")
        
        if workflow_id in self.workflow_subscriptions:
            clients_count = len(self.workflow_subscriptions[workflow_id])
            logger.info(f"Envoi de notification à {clients_count} clients abonnés au workflow {workflow_id}")
            
            message = json.dumps({
                'type': 'workflow_update',
                'workflow_id': workflow_id,
                'data': data
            })
            logger.debug(f"Contenu de la notification: {message[:200]}..." if len(message) > 200 else f"Contenu de la notification: {message}")
            
            # Envoyer le message à tous les clients abonnés
            sent_count = 0
            for client_id in self.workflow_subscriptions[workflow_id]:
                if client_id in self.clients:
                    try:
                        await self.clients[client_id].send(message)
                        sent_count += 1
                        logger.debug(f"Notification envoyée avec succès au client {client_id}")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'envoi de la notification au client {client_id}: {e}")
                        logger.error(traceback.format_exc())
                else:
                    logger.warning(f"Client {client_id} abonné au workflow {workflow_id} n'est plus connecté")
            
            logger.info(f"Notification envoyée à {sent_count}/{clients_count} clients pour le workflow {workflow_id}")
        else:
            logger.warning(f"Aucun client abonné au workflow {workflow_id}")
            logger.debug(f"Abonnements actuels: {self.workflow_subscriptions}")
            logger.debug(f"Clients connectés: {list(self.clients.keys())}")
            logger.debug(f"Données de notification ignorées: {data}")

    
    async def handle_client(self, websocket, path):
        """Gère les connexions client."""
        logger.debug(f"Nouvelle connexion client reçue depuis {websocket.remote_address}")
        client_id = await self.register(websocket)
        
        try:
            async for message in websocket:
                logger.debug(f"Message reçu du client {client_id}: {message[:100]}..." if len(message) > 100 else f"Message reçu du client {client_id}: {message}")
                try:
                    data = json.loads(message)
                    action = data.get('action')
                    logger.debug(f"Action du client {client_id}: {action}")
                    
                    if action == 'subscribe':
                        workflow_id = data.get('workflow_id')
                        if workflow_id:
                            logger.info(f"Client {client_id} s'abonne au workflow {workflow_id}")
                            await self.subscribe_to_workflow(client_id, workflow_id)
                            response = json.dumps({
                                'type': 'subscription_confirmation',
                                'workflow_id': workflow_id,
                                'status': 'success'
                            })
                            logger.debug(f"Envoi de confirmation d'abonnement au client {client_id}: {response}")
                            await websocket.send(response)
                        else:
                            logger.warning(f"Client {client_id} a tenté de s'abonner sans spécifier de workflow_id")
                    else:
                        logger.warning(f"Action inconnue reçue du client {client_id}: {action}")
                    
                    # Autres actions possibles...
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Message JSON invalide reçu du client {client_id}: {e}")
                    error_response = json.dumps({
                        'type': 'error',
                        'message': 'Format de message invalide'
                    })
                    await websocket.send(error_response)
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du message du client {client_id}: {e}")
                    logger.error(traceback.format_exc())
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Connexion fermée pour le client {client_id}: code={e.code}, raison={e.reason}")
        except Exception as e:
            logger.error(f"Erreur inattendue pour le client {client_id}: {e}")
            logger.error(traceback.format_exc())
        finally:
            logger.info(f"Désenregistrement du client {client_id}")
            await self.unregister(client_id)
    
    async def start(self):
        """Démarre le serveur WebSocket."""
        try:
            logger.debug(f"Tentative de démarrage du serveur WebSocket sur {self.host}:{self.port}")
            self.server = await websockets.serve(
                self.handle_client, self.host, self.port
            )
            logger.info(f"Serveur WebSocket démarré avec succès sur {self.host}:{self.port}")
            
            # Garder le serveur en cours d'exécution
            await self.server.wait_closed()
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du serveur WebSocket: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def start_server(self):
        """Démarre le serveur dans une boucle asyncio."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            logger.info("Arrêt du serveur WebSocket")
        finally:
            loop.close()
    
    def stop(self):
        """Arrête le serveur WebSocket."""
        if self.server:
            self.server.close()
            logger.info("Serveur WebSocket arrêté")

# Instance globale du serveur WebSocket
_ws_server_instance = None

def get_ws_server():
    """Retourne l'instance du serveur WebSocket."""
    global _ws_server_instance
    if _ws_server_instance is None:
        _ws_server_instance = WebSocketServer()
    return _ws_server_instance
