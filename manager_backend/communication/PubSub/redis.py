import redis
import threading
import json
from redis import ConnectionError
from redis import RedisError
from django.conf import settings


class RedisPubSubManager:
    def __init__(self, host=settings.REDIS_HOST or '192.168.1.105', port=settings.REDIS_PORT or 6380, db=settings.REDIS_DB, channels=settings.REDIS_CHANNELS):
        self.host = host
        self.port = int(port) if isinstance(port, str) else port
        self.db = db
        self.redis_client = None
        self.pubsub = None
        self.channels = channels or [
            'auth/login_response',
            'auth/register_response'
        ]
        self.subscribed = False
        self.listener_thread = None

       
   
    def connect(self):
        """Établit une connexion au broker Redis."""
        try:
            self.redis_client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            print(f"[INFO] Connexion établie à Redis sur {self.host}:{self.port}, DB: {self.db}")
        except ConnectionError as e:
            print(f"[ERROR] Impossible de se connecter à Redis : {e}")
            raise ConnectionError(f"Erreur de connexion à Redis : {e}")
        except RedisError as e:
            print(f"[ERROR] Erreur Redis : {e}")
            raise RedisError(f"Erreur Redis : {e}")

    def subscribe(self, callback):
        """Souscrit aux canaux et démarre l'écoute avec le callback."""
        try:
            if not self.redis_client:
                raise ConnectionError("Connexion Redis manquante.")
            if not self.channels:
                raise ValueError("Aucun canal spécifié pour la souscription.")

            # Souscription aux canaux - correction pour éviter d'utiliser une liste comme clé
            subscription_dict = {}
            for channel in self.channels:
                subscription_dict[channel] = callback
                
            self.pubsub.subscribe(**subscription_dict)
            self.subscribed = True
            print(f"[INFO] Souscrit aux canaux : {', '.join(self.channels)}")

            # Démarre le thread d'écoute
            if not self.listener_thread or not self.listener_thread.is_alive():
                self.listener_thread = threading.Thread(target=self._listen, daemon=True)
                self.listener_thread.start()
        except ConnectionError as e:
            print(f"[ERROR] Impossible de se connecter à Redis : {e}")
            raise ConnectionError(f"Erreur de connexion à Redis : {e}")
        except RedisError as e:
            print(f"[ERROR] Erreur Redis : {e}")
            raise RedisError(f"Erreur Redis : {e}")

    def _listen(self):
        """Boucle d'écoute des messages."""
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel']
                data = message['data']
                
                print(f"[INFO] Message reçu sur le canal {channel}")
                
                # Récupérer le callback pour ce canal
                callback_found = False
                for ch, callback in self.pubsub.channels.items():
                    if ch.decode('utf-8') == channel:
                        # Appeler le callback avec les données brutes
                        # La fonction handle_message s'occupera de formater le message
                        try:
                            callback(data)
                            callback_found = True
                        except Exception as e:
                            print(f"[ERROR] Erreur lors de l'appel du callback pour {channel}: {e}")
                            import traceback
                            traceback.print_exc()
                
                if not callback_found:
                    print(f"[WARNING] Aucun callback trouvé pour le canal {channel}")

    def publish(self, channel, message):
        """Publie un message sur un canal."""
        try:
            if not self.redis_client:
                raise ConnectionError("Connexion Redis manquante.")
            if not channel or not message:
                raise ValueError("Canal ou message manquant.")

            self.redis_client.publish(channel, message)
            print(f"[INFO] Message publié sur {channel}: {message}")
        except ConnectionError as e:
            print(f"[ERROR] Impossible de se connecter à Redis : {e}")
            raise ConnectionError(f"Erreur de connexion à Redis : {e}")
        except RedisError as e:
            print(f"[ERROR] Erreur Redis : {e}")
            raise RedisError(f"Erreur Redis : {e}")



    def unsubscribe_channel(self, channel):
        """Se désabonne d'un canal spécifique."""

        try:
            if not self.pubsub:
                raise ConnectionError
            if channel not in self.channels:
                raise ValueError(f"Canal {channel} non souscrit.")
            self.pubsub.unsubscribe(channel)
            self.channels.remove(channel)
            print(f"[INFO] Désabonné du canal : {channel}")
        except ConnectionError as e:
            print(f"[ERROR] Impossible de se désabonner du canal {channel} : {e}")
            raise ConnectionError(f"Erreur de désabonnement du canal {channel} : {e}")
        except ValueError as e:
            print(f"[ERROR] Erreur de désabonnement : {e}")
            raise ValueError(f"Erreur de désabonnement : {e}")

    def unsubscribe_all(self):
        """Se désabonne de tous les canaux."""
        if self.pubsub:
            self.pubsub.unsubscribe()
            self.channels = []
            self.subscribed = False
            print("[INFO] Désabonné de tous les canaux.")


    def close(self):
        """Ferme proprement la connexion et les souscriptions."""
        self.unsubscribe_all()
        if self.pubsub:
            self.pubsub.close()
        self.redis_client = None
        self.pubsub = None
        print("[INFO] Connexion Redis fermée.")
