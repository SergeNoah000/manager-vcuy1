# backend/workflows/views.py
from django.utils import timezone  # Modifiez cette ligne
import json
import os
import uuid

from django.conf import settings
from rest_framework import viewsets
from communication.PubSub.get_redis_instance import get_redis_manager
from .models import Workflow, WorkflowStatus  # Ajoutez WorkflowStatus ici
from .serializers import WorkflowSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticated as permissions
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.core.exceptions import ObjectDoesNotExist
from .serializers import WorkflowSerializer, UserSerializer, RegisterSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer
import json
import traceback


from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework.authtoken.views import ObtainAuthToken

User = get_user_model()
from django.views.decorators.csrf import csrf_exempt

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all().order_by('-created_at')
    serializer_class = WorkflowSerializer
    permission_classes = [AllowAny]  # Allow any user to access this view


@csrf_exempt
def submit_workflow_view(request, workflow_id):
    """
    View to submit a workflow for processing.
    """
    try:
        workflow = get_object_or_404(Workflow, id=workflow_id)
        # Check if the workflow is in a valid state for submission
        if workflow.status != WorkflowStatus.CREATED:
            return JsonResponse({'error': 'Workflow is not in a valid state for submission.'}, status=400)

        # Préparer les données pour Redis
        data = {
            # All workflow data
            'workflow_id': str(workflow.id),
            'workflow_name': workflow.name,
            'workflow_description': workflow.description,
            'workflow_status': workflow.status,
            'created_at': workflow.created_at.isoformat() if hasattr(workflow.created_at, 'isoformat') else str(workflow.created_at),
            'workflow_type': workflow.workflow_type,
            'owner': {
                'username': workflow.owner.username,
                'email': workflow.owner.email
            },
            "priority": workflow.priority,
            "estimated_resources": workflow.estimated_resources,
            "max_execution_time": workflow.max_execution_time,
            "input_data_size": workflow.input_data_size,
            "retry_count": workflow.retry_count,
            "submitted_at": timezone.now().isoformat(),
        }

        # Générer un request_id
        request_id = str(uuid.uuid4())
        data["request_id"] = request_id

        try:
            # Tentative de connexion à Redis (qui échouera probablement)
            pubsub_manager = get_redis_manager()
            # Convertir les données en JSON pour Redis
            json_data = json.dumps(data)
            pubsub_manager.publish("WORKFLOW_SUBMISSION", json_data)
            print(f"[INFO] Workflow submission message published with request_id: {request_id}")
        except Exception as e:
            # Capturer l'erreur Redis et la logger, mais continuer l'exécution
            print(f"[WARNING] Redis connection failed: {e}")
            # En développement, nous continuons comme si Redis avait fonctionné

        try:
            # Enregistrer request_id dans un fichier, indépendamment de Redis
            registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "registration_request_id.json")
            with open(registration_request_id_path, "w") as f:
                json.dump({"request_id": request_id}, f)
            print(f"[INFO] request_id saved in {registration_request_id_path}")
        except Exception as e:
            # Capturer l'erreur de fichier et la logger
            print(f"[WARNING] Failed to save request_id to file: {e}")

        # Update the workflow status to SUBMITTED
        workflow.status = WorkflowStatus.SUBMITTED
        workflow.submitted_at = timezone.now()

        # Save the workflow instance
        workflow.save()

        return JsonResponse({'message': 'Workflow submitted successfully (Note: Redis connection failed but workflow was updated).'}, status=200)
    except Workflow.DoesNotExist:
        return JsonResponse({'error': 'Workflow not found.'}, status=404)
    
class RegisterView(APIView):
    # TRÈS IMPORTANT: AllowAny est nécessaire pour permettre l'inscription!
    permission_classes = [AllowAny]
    authentication_classes = []  # Pas d'authentification nécessaire pour s'inscrire

    def post(self, request):
        # Log des données pour le débogage (sans exposer le mot de passe)
        request_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'password' in request_data:
            request_data['password'] = '********'
        if 'password2' in request_data:
            request_data['password2'] = '********'
        
        print(f"[DEBUG] Données reçues pour l'inscription: {request_data}")
        print(f"[DEBUG] Type de request.data: {type(request.data)}")
        
        try:
            # Si les données arrivent en tant que chaîne JSON, les parser
            if isinstance(request.data, str):
                data = json.loads(request.data)
            else:
                data = request.data
            
            serializer = RegisterSerializer(data=data)
            
            if serializer.is_valid():
                print("[DEBUG] Données d'inscription valides")
                
                # Création de l'utilisateur
                try:
                    user = serializer.save()
                    print(f"[DEBUG] Utilisateur créé avec succès: {user.email}")
                    
                    # Création du token
                    token, created = Token.objects.get_or_create(user=user)
                    print(f"[DEBUG] Token {'créé' if created else 'récupéré'}: {token.key}")
                    
                    # Construction de la réponse
                    response_data = {
                        "user": {
                            "id": str(user.id),
                            "username": user.username,
                            "email": user.email
                        },
                        "token": token.key
                    }
                    
                    print(f"[DEBUG] Réponse d'inscription réussie: {response_data}")
                    return Response(response_data, status=status.HTTP_201_CREATED)
                except Exception as e:
                    print(f"[ERROR] Exception lors de la création de l'utilisateur: {str(e)}")
                    print(traceback.format_exc())
                    return Response({"error": f"Erreur lors de la création de l'utilisateur: {str(e)}"}, 
                                   status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                print(f"[DEBUG] Erreurs de validation: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"[ERROR] Exception non gérée dans RegisterView: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": f"Une erreur inattendue s'est produite: {str(e)}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    # TRÈS IMPORTANT: AllowAny est nécessaire pour permettre la connexion!
    permission_classes = [AllowAny]
    authentication_classes = []  # Pas d'authentification nécessaire pour se connecter

    def post(self, request):
        try:
            # Log des données pour le débogage (sans exposer le mot de passe)
            request_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            if 'password' in request_data:
                request_data['password'] = '********'
            
            print(f"[DEBUG] Données reçues pour la connexion: {request_data}")
            
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                return Response({
                    'error': 'Veuillez fournir un email et un mot de passe'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer l'utilisateur par email
            try:
                user = User.objects.get(email=email)
                print(f"[DEBUG] Utilisateur trouvé: {user.email}")
                
                if user.check_password(password):
                    # Connexion réussie
                    token, created = Token.objects.get_or_create(user=user)
                    print(f"[DEBUG] Connexion réussie pour: {user.email}, Token: {token.key}")
                    
                    return Response({
                        'token': token.key,
                        'user': {
                            'id': str(user.id),
                            'email': user.email,
                            'username': user.username
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    # Mot de passe incorrect
                    print(f"[DEBUG] Mot de passe incorrect pour: {user.email}")
                    return Response({
                        'error': 'Identifiants incorrects'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                # Utilisateur non trouvé
                print(f"[DEBUG] Utilisateur non trouvé pour l'email: {email}")
                return Response({
                    'error': 'Identifiants incorrects'
                }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(f"[ERROR] Exception non gérée dans LoginView: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": f"Une erreur inattendue s'est produite: {str(e)}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Seuls les utilisateurs authentifiés peuvent se déconnecter

    def post(self, request):
        try:
            # Si utilisation de tokens, supprimer le token
            if request.auth and hasattr(request.auth, 'delete'):
                request.auth.delete()
                print(f"[DEBUG] Token supprimé pour l'utilisateur: {request.user.email}")
            
            return Response({"success": "Déconnexion réussie"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"[ERROR] Erreur lors de la déconnexion: {str(e)}")
            return Response({"error": "Erreur lors de la déconnexion"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)