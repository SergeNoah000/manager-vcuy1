import threading
from .redis import RedisPubSubManager
import os

redis_instance = None
redis_thread = None
lock = threading.Lock()

def initialize_redis_manager():
    """Initialise l'instance de RedisPubSubManager dans un thread."""
    global redis_instance
    with lock:
        if redis_instance is None:
            redis_instance = RedisPubSubManager()
            redis_instance.connect()
            print("[INFO] RedisPubSubManager initialisé avec succès.")
        
def get_redis_manager():
    """Renvoie une instance de RedisPubSubManager, initialisée dans un thread."""
    global redis_thread
    if redis_thread is None or not redis_thread.is_alive():
        redis_thread = threading.Thread(target=initialize_redis_manager)
        redis_thread.start()
        redis_thread.join()  # Optionnel : attendre que le thread termine l'initialisation
    return redis_instance