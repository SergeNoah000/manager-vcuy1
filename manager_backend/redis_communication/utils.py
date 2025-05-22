"""
Utilitaires divers pour le module de communication Redis.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
import jwt
from django.conf import settings
from .exceptions import NoLoginError
logger = logging.getLogger(__name__)

def generate_token(client_id: str, client_type: str, expiration_hours: int = 24) -> str:
    """
    Génère un token JWT pour l'authentification.
    
    Args:
        client_id: ID du client
        client_type: Type de client (coordinator, manager, volunteer)
        expiration_hours: Durée de validité en heures
        
    Returns:
        str: Token JWT
    """
    secret_key = getattr(settings, 'SECRET_KEY', 'default-secret-key')
    
    payload = {
        'client_id': client_id,
        'client_type': client_type,
        'exp': int(time.time()) + expiration_hours * 3600,
        'iat': int(time.time())
    }
    
    return jwt.encode(payload, secret_key, algorithm='HS256')

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Vérifie un token JWT.
    
    Args:
        token: Token JWT à vérifier
        
    Returns:
        Dict ou None: Payload du token si valide, None sinon
    """
    secret_key = getattr(settings, 'SECRET_KEY', 'default-secret-key')
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expiré")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Token invalide")
        return None

def format_timestamp(timestamp: float) -> str:
    """
    Formate un timestamp en chaîne ISO 8601.
    
    Args:
        timestamp: Timestamp UNIX
        
    Returns:
        str: Chaîne au format ISO 8601
    """
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).isoformat()


def get_manager_login_token():
    """
    Recuper le token stoker dans le json .manager/manager_login_info.json et provoque une erreur NoLoginError si le fichier n'est pas trouvé
    """
    try:
        with open('.manager/manager_login_info.json', 'r') as f:
            data = json.load(f)
            return data['token']
    except FileNotFoundError:
        raise NoLoginError("Le fichier .manager/manager_login_info.json n'a pas été trouvé")