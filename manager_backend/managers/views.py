from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Manager
from .serializers import ManagerSerializer, ManagerRegistrationSerializer
import json
import uuid
import os
import platform
import psutil
from django.conf import settings
from django.utils import timezone
from communication.PubSub.get_redis_instance import get_redis_manager

class ManagerViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les opérations CRUD sur les managers.
    Permet de créer, lire, mettre à jour et supprimer des managers.
    """
    queryset = Manager.objects.all()
    serializer_class = ManagerSerializer
    permission_classes = [permissions.AllowAny]  # À remplacer par une permission appropriée en production
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'register':
            return ManagerRegistrationSerializer
        return ManagerSerializer
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Endpoint pour l'enregistrement d'un nouveau manager.
        Envoie également un message au coordinateur via Redis.
        """
        try:
            # Récupérer les données de la requête
            username = request.data.get('username', 'yves')
            email = request.data.get('email', 'yves@manager_app.com')
            password = request.data.get('password', 'yves')
            
            # Créer le manager directement
            manager = Manager.objects.create(
                username=username,
                email=email,
                password=password,
                status='inactive'
            )
            
            # Générer un request_id unique
            request_id = str(uuid.uuid4())
            
            # Créer le dossier .manager_app s'il n'existe pas
            manager_app_path = os.path.join(settings.BASE_DIR, ".manager_app")
            if not os.path.exists(manager_app_path):
                os.makedirs(manager_app_path)
            
            # Enregistrer le request_id dans un fichier pour le retrouver plus tard
            registration_request_id_path = os.path.join(manager_app_path, "registration_request_id.json")
            with open(registration_request_id_path, "w") as f:
                json.dump({"request_id": request_id}, f)
            
            # Préparer le message à envoyer exactement comme attendu par le coordinateur
            message = {
                "request_id": request_id,
                "username": manager.username, 
                "email": manager.email, 
                "password": password,
                "status": manager.status
                
            }          
            
            # Obtenir l'instance Redis et publier le message
            try:
                print("[DEBUG] Tentative d'envoi du message d'enregistrement au coordinateur...")
                print(f"[DEBUG] Message: {json.dumps(message)}")
                print(f"[DEBUG] Canal: auth/register")
                
                # Créer une nouvelle instance Redis directement pour le proxy Redis du coordinateur
                from redis import Redis
                # Utiliser le port 6380 qui est celui du proxy Redis du coordinateur
                redis_client = Redis(host='127.0.0.1', port=6380, db=0, decode_responses=True)
                print(f"[DEBUG] Connexion Redis établie à 127.0.0.1:6380")
                
                # Publier le message sur le canal auth/register
                result = redis_client.publish("auth/register", json.dumps(message))
                print(f"[DEBUG] Message publié sur le canal auth/register avec résultat: {result}")
                
                # Attendre une réponse sur le canal auth/register_response
                print("[DEBUG] En attente de réponse sur le canal auth/register_response...")
                pubsub = redis_client.pubsub()
                pubsub.subscribe('auth/register_response')
                
                # Attendre la réponse pendant 5 secondes maximum (augmenté pour plus de fiabilité)
                import time
                start_time = time.time()
                response_data = None
                
                while time.time() - start_time < 5:
                    response_message = pubsub.get_message(timeout=0.1)
                    if response_message and response_message['type'] == 'message':
                        print(f"[DEBUG] Réponse reçue: {response_message['data']}")
                        try:
                            response_data = json.loads(response_message['data'])
                            break
                        except json.JSONDecodeError:
                            print(f"[ERROR] Impossible de décoder la réponse JSON: {response_message['data']}")
                    time.sleep(0.1)
                
                # Initialiser les variables de réponse
                response_status = None
                response_message = None
                
                # Traiter la réponse si elle a été reçue
                if response_data:
                    response_status = response_data.get('status')
                    response_message = response_data.get('message')
                    
                    if response_status == 'success':
                        # Mettre à jour le manager local avec l'ID du coordinateur
                        coordinator_manager_id = response_data.get('manager_id')
                        if coordinator_manager_id:
                            manager.coordinator_manager_id = coordinator_manager_id
                            manager.save()
                            print(f"[INFO] Manager mis à jour avec l'ID du coordinateur: {coordinator_manager_id}")
                            
                            # Enregistrer les informations dans le fichier .manager_app/manager_info.json
                            manager_app_path = os.path.join(settings.BASE_DIR, ".manager_app")
                            manager_info_path = os.path.join(manager_app_path, "manager_info.json")
                            
                            manager_info = {
                                "manager_id": coordinator_manager_id,
                                "username": manager.username,
                                "email": manager.email,
                                "password": password,  # Stocké pour la communication automatique
                                "timestamp": response_data.get('timestamp')
                            }
                            
                            with open(manager_info_path, "w") as f:
                                json.dump(manager_info, f)
                            
                            print(f"[INFO] Informations du manager enregistrées dans {manager_info_path}")
                    else:
                        print(f"[WARNING] Enregistrement non réussi: {message}")
            except Exception as e:
                print(f"[ERROR] Erreur lors de la publication du message: {e}")
                import traceback
                traceback.print_exc()
            
            # Préparer la réponse en fonction du résultat de l'enregistrement au coordinateur
            if response_data and response_status == 'success':
                return Response(
                {
                    "message": "Manager registered successfully and synchronized with coordinator.",
                    "manager": ManagerSerializer(manager).data,
                    "coordinator_id": str(manager.coordinator_manager_id)
                },
                status=status.HTTP_201_CREATED
            )
            else:
                return Response(
                {
                    "message": "Manager registered locally but synchronization with coordinator may be incomplete.",
                    "manager": ManagerSerializer(manager).data,
                    "coordinator_response": response_data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            # En cas d'erreur lors de la création du manager ou de l'envoi du message
            return Response(
                {
                    "message": "Failed to register manager.",
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Endpoint pour la connexion d'un manager existant.
        Envoie également un message au coordinateur via Redis.
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            manager = Manager.objects.get(username=username)
        except Manager.DoesNotExist:
            return Response(
                {"error": "Manager not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier si le manager a un coordinator_manager_id
        if not manager.coordinator_manager_id:
            return Response(
                {"error": "Manager not registered with coordinator yet."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Envoyer le message de connexion au coordinateur via Redis
        try:
            # Générer un request_id unique
            request_id = str(uuid.uuid4())
            
            # Préparer le message à envoyer
            message = {
                "request_id": request_id,
                "username": manager.username,
                "password": password,
                "manager_id": str(manager.coordinator_manager_id)
            }
            
            # Obtenir l'instance Redis et publier le message
            redis_manager = get_redis_manager()
            redis_manager.connect()
            redis_manager.publish("auth/login", json.dumps(message))
            
            # Mettre à jour la date de dernière connexion
            manager.last_login = timezone.now()
            manager.save()
            
            return Response(
                {"message": "Login request sent to coordinator.",
                 "manager": ManagerSerializer(manager).data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to send login request to coordinator: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
