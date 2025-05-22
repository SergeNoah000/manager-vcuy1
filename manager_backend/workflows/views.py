# backend/workflows/views.py
import json
from rest_framework import viewsets
from .models import Workflow, WorkflowStatus
from .serializers import WorkflowSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets,  status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import WorkflowSerializer, RegisterSerializer
import traceback
from django.views.decorators.csrf import csrf_exempt
import logging
from redis_communication.client import RedisClient


logger = logging.getLogger(__name__)



class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all().order_by('-created_at')
    serializer_class = WorkflowSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
def submit_workflow_view(request, workflow_id):
    """
    View to submit a workflow for processing.
    """
    try:
        # Récupérer le workflow
        workflow = get_object_or_404(Workflow, id=workflow_id)
        
        # Notifier le début du processus de soumission
        from websocket_service.client import notify_event
        notify_event('workflow_status_change', {
            'workflow_id': str(workflow_id),
            'status': 'SUBMITTING',
            'message': 'Soumission du workflow en cours...'
        })
        
        # Utiliser le gestionnaire de workflow pour soumettre le workflow
        from workflows.handlers import submit_workflow_handler
        success, response = submit_workflow_handler(str(workflow_id))
        logger.info(f"Submit workflow response: {response}")
        
        if not success:
            # Notifier l'échec de la soumission
            notify_event('workflow_status_change', {
                'workflow_id': str(workflow_id),
                'status': 'SUBMISSION_FAILED',
                'message': f"Échec de la soumission: {response.get('message', 'Erreur inconnue')}"
            })
            return JsonResponse({'success': False, 'response': response}, status=400)
            
        # Soumission réussie, mettre à jour le statut et notifier
        workflow.status = WorkflowStatus.SPLITTING
        workflow.save()
        logger.info(f"Workflow {workflow_id} soumis avec succès")
        
        # Notifier la réussite de la soumission
        notify_event('workflow_status_change', {
            'workflow_id': str(workflow_id),
            'status': 'SPLITTING',
            'message': 'Soumission réussie, découpage en cours...'
        })
        
        # Réponse initiale au client HTTP
        response_data = {'success': True, 'message': 'Workflow soumis avec succès, traitement en cours'}
        
        # Lancer le découpage dans un thread séparé pour ne pas bloquer la réponse HTTP
        def process_workflow_async():
            try:
                # Découpage du workflow
                logger.info(f"Lancement du découpage")
                from workflows.split_workflow import split_workflow
                tasks = split_workflow(str(workflow_id), workflow.workflow_type)
                logger.info(f"Tasks: {len(tasks) if tasks else 0} créées")
                
                # Notifier la fin du découpage
                notify_event('workflow_status_change', {
                    'workflow_id': str(workflow_id),
                    'status': 'SPLIT_COMPLETED',
                    'message': f'Découpage terminé, {len(tasks) if tasks else 0} tâches créées'
                })
                
                # Mettre à jour le statut du workflow
                if response.get('volunteers'):
                    workflow.status = WorkflowStatus.ASSIGNING
                    workflow.save()
                    
                    # Notifier le début de l'assignation
                    notify_event('workflow_status_change', {
                        'workflow_id': str(workflow_id),
                        'status': 'ASSIGNING',
                        'message': 'Attribution des tâches aux volontaires...'
                    })
                    
                    logger.info(f"Lancement de l'assignment")
                    from tasks.scheduller import assign_workflow_to_volunteers
                    assign_workflow_to_volunteers(workflow, response.get('volunteers'))
                    logger.info(f"Assignment effectué avec succès")
                    
                    # Notifier la fin de l'assignation
                    notify_event('workflow_status_change', {
                        'workflow_id': str(workflow_id),
                        'status': 'ASSIGNED',
                        'message': 'Tâches attribuées avec succès'
                    })
                else:
                    logger.info(f"Volunteers non reçus, lancement de l'écoute sur le canal d'assignment")
                    pubsub = RedisClient.get_instance()
                    pubsub.subscribe('workflow/assignment')
                    
                    # Notifier l'attente de volontaires
                    notify_event('workflow_status_change', {
                        'workflow_id': str(workflow_id),
                        'status': 'WAITING_VOLUNTEERS',
                        'message': 'En attente de volontaires disponibles...'
                    })
                
                # Lancer l'attribution des tâches
                from tasks.scheduller import assign_tasks_fcfs
                assign_tasks_fcfs(str(workflow_id))
                
                # Notifier la fin du processus complet
                notify_event('workflow_status_change', {
                    'workflow_id': str(workflow_id),
                    'status': workflow.status,
                    'message': 'Processus de soumission terminé'
                })
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement asynchrone du workflow: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Notifier l'erreur
                notify_event('workflow_status_change', {
                    'workflow_id': str(workflow_id),
                    'status': 'ERROR',
                    'message': f'Erreur lors du traitement: {str(e)}'
                })
        
        # Démarrer le traitement asynchrone
        import threading
        thread = threading.Thread(target=process_workflow_async)
        thread.daemon = True
        thread.start()
        
        # Retourner immédiatement une réponse au client HTTP
        return JsonResponse(response_data, status=200)
            
    except Workflow.DoesNotExist:
        logger.error(f"Workflow {workflow_id} non trouvé")
        return JsonResponse({'error': 'Workflow not found.'}, status=404)
    except Exception as e:
        import traceback
        logger.error(f"Erreur inattendue lors de la soumission du workflow {workflow_id}: {e}")
        logger.error(traceback.format_exc())
        
        # Notifier l'erreur via WebSocket
        try:
            from websocket_service.client import notify_event
            notify_event('workflow_status_change', {
                'workflow_id': str(workflow_id),
                'status': 'ERROR',
                'message': f'Erreur inattendue: {str(e)}'
            })
        except Exception:
            pass  # Ne pas échouer si la notification échoue
            
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)
    
class RegisterView(APIView):
    # TRÈS IMPORTANT: AllowAny est nécessaire pour permettre l'inscription!
    permission_classes = [AllowAny]
    authentication_classes = []  # Pas d'authentification nécessaire pour s'inscrire

    def post(self, request):

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
                    
                    # Construction de la réponse
                    response_data = {
                        "user": {
                            "id": str(user.id),
                            "username": user.username,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
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
                            'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name
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