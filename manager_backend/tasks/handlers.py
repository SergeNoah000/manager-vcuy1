"""
Gestionnaires d'événements pour les messages Redis.
Inclut les gestionnaires pour l'authentification des managers et des volontaires.
"""

import logging
import json
from math import log
from django.conf import settings
from django.utils import timezone
from redis_communication.message import Message
logger = logging.getLogger(__name__)




def handle_task_accept(channel: str, message: Message):
    """
    Gestionnaire pour l'écoute des messages de type 'task/accept'.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
        
    Returns:
        True si le message a été traité avec succès, False sinon
    """
    logger.info(f"Reçu un message de type 'task/accept' sur le canal {channel}")
    logger.debug(f"Contenu du message: {message.data}")
    
    # Récupérer les informations
    data = message.data
    
    # Vérifier que le message contient les informations nécessaires
    if 'workflow_id' not in data or 'task_id' not in data or 'volunteer_id' not in data:
        logger.error("Le message ne contient pas les informations nécessaires (workflow_id, task_id, volunteer_id)")
        return False
    
    workflow_id = data['workflow_id']
    task_id = data['task_id']
    volunteer_id = data['volunteer_id']
    
    logger.info(f"Traitement de l'acceptation de la tâche {task_id} par le volontaire {volunteer_id} pour le workflow {workflow_id}")
    
    try:
        # Importer les modèles nécessaires
        from workflows.models import Workflow, WorkflowStatus
        from tasks.models import Task, TaskStatus
        from volunteers.models import Volunteer, VolunteerTask
        
        # Récupérer les objets
        workflow = Workflow.objects.get(id=workflow_id)
        task = Task.objects.get(id=task_id)
        volunteer = Volunteer.objects.get(coordinator_volunteer_id=volunteer_id)

        # Verifier si le workflow est en cours
        if workflow.status != WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.RUNNING
            workflow.save()
            
        # Verifier si la tâche est en cours
        if task.status != TaskStatus.RUNNING:
            task.status = TaskStatus.RUNNING
            task.save()
            
        # Vérifier si la tâche est déjà assignée à ce volontaire
        volunteer_task = VolunteerTask.objects.filter(task=task, volunteer=volunteer).first()
        
        if volunteer_task:
            # Mettre à jour le statut de l'assignation
            volunteer_task.status = "STARTED"
            volunteer_task.started_at = timezone.now()
            volunteer_task.save()
            logger.info(f"Assignation existante mise à jour: tâche {task.name} acceptée par le volontaire {volunteer.name}")
        else:
            # Créer une nouvelle assignation
            volunteer_task = VolunteerTask.objects.create(
                task=task,
                volunteer=volunteer,
                assigned_at=timezone.now(),
                started_at=timezone.now(),
                status="STARTED"
            )
            logger.info(f"Nouvelle assignation créée: tâche {task.name} acceptée par le volontaire {volunteer.name}")
        
        # Mettre à jour le statut de la tâche
        task.status = "RUNNING"
        task.save()
        logger.info(f"Statut de la tâche {task.name} mis à jour: RUNNING")
        
        # Notifier le changement de statut via WebSocket
        from websocket_service.client import notify_event
        notify_event('task_status_change', {
            'workflow_id': str(workflow.id),
            'task_id': str(task.id),
            'status': 'RUNNING',
            'volunteer': volunteer.name,
            'message': f"Tâche {task.name} démarrée par {volunteer.name}"
        })
        
        return True
        
    except Workflow.DoesNotExist:
        logger.error(f"Le workflow {workflow_id} n'existe pas")
    except Task.DoesNotExist:
        logger.error(f"La tâche {task_id} n'existe pas")
    except Volunteer.DoesNotExist:
        logger.error(f"Le volontaire {volunteer_id} n'existe pas")
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'acceptation de la tâche: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return False




def handle_task_progress(channel: str, message: Message):
    """
    Gere la reception de la progression des taches via le cannal 'task/progress'

    Args:
        channel (str): Nom du cannal 'task/progress'
        message (Message): Message recu
    """

    logger.info("Progression de tache recu")
    logger.warning(f"Contenu du message: {message.data}")

    try:
        # Récupérer les informations
        data = message.data
        
        # Vérifier que le message contient les informations nécessaires
        if 'workflow_id' not in data or 'task_id' not in data or 'volunteer_id' not in data:
            logger.error("Le message ne contient pas les informations nécessaires (workflow_id, task_id, volunteer_id)")
            return False
        
        workflow_id = data['workflow_id']
        task_id = data['task_id']
        volunteer_id = data['volunteer_id']
        progress = data['progress']


        # Récupérer les objets

        from workflows.models import Workflow
        from tasks.models import Task
        from volunteers.models import Volunteer, VolunteerTask
        workflow = Workflow.objects.get(id=workflow_id)
        task = Task.objects.get(id=task_id)
        volunteer = Volunteer.objects.get(coordinator_volunteer_id=volunteer_id)


                
            # Vérifier si la tâche est déjà assignée à ce volontaire
        volunteer_task = VolunteerTask.objects.filter(task=task, volunteer=volunteer).first()


        if volunteer_task:
            # Mettre à jour le statut de l'assignation
            volunteer_task.progress = progress
            volunteer_task.save()
            logger.info(f"Assignation mise à jour: tâche {task.name} en cours par le volontaire {volunteer.name}")
            return True

        else:
            # Generer un message d'erreur
            logger.error(f"Pas d'assignation de tache entre le volontaire {volunteer.name} et la tache {task.name}")
            return False
    except Workflow.DoesNotExist:
        logger.error(f"Le workflow {workflow_id} n'existe pas")
    except Task.DoesNotExist:
        logger.error(f"La tâche {task_id} n'existe pas")
    except Volunteer.DoesNotExist:
        logger.error(f"Le volontaire {volunteer_id} n'existe pas")
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'acceptation de la tâche: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return False



def handle_task_status(channel: str, message: Message):
    """
    Mets à jour le statut de la tache

    Args:
        channel (str): canal
        message (Message): Message recu
    """


    logger.info("Statut de tache recu")
    logger.debug(f"Message de statut recu: {message.data}")

    try:
        # Récupérer les informations
        data = message.data
        
        # Vérifier que le message contient les informations nécessaires
        if 'workflow_id' not in data or 'task_id' not in data or 'volunteer_id' not in data:
            logger.error("Le message ne contient pas les informations nécessaires (workflow_id, task_id, volunteer_id)")
            return False
        
        workflow_id = data['workflow_id']
        task_id = data['task_id']
        volunteer_id = data['volunteer_id']
        status = data['status']


        # Récupérer les objets

        from workflows.models import Workflow
        from tasks.models import Task
        from volunteers.models import Volunteer, VolunteerTask
        workflow = Workflow.objects.get(id=workflow_id)
        task = Task.objects.get(id=task_id)
        volunteer = Volunteer.objects.get(coordinator_volunteer_id=volunteer_id)


                
            # Vérifier si la tâche est déjà assignée à ce volontaire
        volunteer_task = VolunteerTask.objects.filter(task=task, volunteer=volunteer).first()


        if volunteer_task:
            # Mettre à jour le statut de l'assignation
            volunteer_task.status = status
            volunteer_task.save()
            logger.info(f"Statut de la tâche mise à jour: tâche {task.name} en cours par le volontaire {volunteer.name}")
            return True

        else:
            # Generer un message d'erreur
            logger.error(f"Pas d'assignation de tache entre le volontaire {volunteer.name} et la tache {task.name}")
            return False
    except Workflow.DoesNotExist:
        logger.error(f"Le workflow {workflow_id} n'existe pas")
    except Task.DoesNotExist:
        logger.error(f"La tâche {task_id} n'existe pas")
    except Volunteer.DoesNotExist:
        logger.error(f"Le volontaire {volunteer_id} n'existe pas")
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'acceptation de la tâche: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return False
    







def handle_task_complete(channel: str, message: Message):
    """
    Gestionnaire pour l'écoute des messages de type 'task/complete'.
    
    Args:
        channel: Canal sur lequel le message a été reçu
        message: Message reçu
        
    Returns:
        True si le message a été traité avec succès, False sinon
    """
    logger.info(f"Reçu un message de type 'task/complete' sur le canal {channel}")
    logger.debug(f"Contenu du message: {message.data}")
    
    # Récupérer les informations
    data = message.data
    
    # Vérifier que le message contient les informations nécessaires
    if 'workflow_id' not in data or 'task_id' not in data or 'volunteer_id' not in data:
        logger.error("Le message ne contient pas les informations nécessaires (workflow_id, task_id, volunteer_id)")
        return False
    
    workflow_id = data['workflow_id']
    task_id = data['task_id']
    volunteer_id = data['volunteer_id']
    result = data.get('result', {})
    
    logger.info(f"Traitement de la complétion de la tâche {task_id} par le volontaire {volunteer_id} pour le workflow {workflow_id}")
    
    try:
        # Importer les modèles nécessaires
        from django.utils import timezone
        from workflows.models import Workflow, WorkflowStatus
        from tasks.models import Task, TaskStatus
        from volunteers.models import Volunteer, VolunteerTask
        
        # Récupérer les objets
        workflow = Workflow.objects.get(id=workflow_id)
        task = Task.objects.get(id=task_id)
        volunteer = Volunteer.objects.get(coordinator_volunteer_id=volunteer_id)
        
        # Récupérer l'assignation de la tâche
        volunteer_task = VolunteerTask.objects.filter(task=task, volunteer=volunteer).first()
        
        if volunteer_task:
            # Mettre à jour le statut de l'assignation
            volunteer_task.status = "COMPLETED"
            volunteer_task.completed_at = timezone.now()
            volunteer_task.result = result
            volunteer_task.progress = 100.0
            volunteer_task.save()
            logger.info(f"Assignation mise à jour: tâche {task.name} complétée par le volontaire {volunteer.name}")

            # Mettre à jour le statut de la tâche
            task.status = TaskStatus.COMPLETED
            task.save()
            logger.info(f"Statut de la tâche {task.name} mis à jour: COMPLETED")

            # Mettre à jour le statut du workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.save()
            logger.info(f"Statut du workflow {workflow.name} mis à jour: COMPLETED")


            # Verifier si c'etait la derniere tache du workflow qui etait en running et qu'il n'y a pas de tache echouée
            running = workflow.tasks.filter(status="RUNNING").count()
            failed = workflow.tasks.filter(status="FAILED").count()
            if running == 0 and failed == 0:
                # Toutes les taches sont complétées, mettre à jour le statut du workflow
                workflow.status = WorkflowStatus.COMPLETED
                workflow.save()
                logger.info(f"Toutes les taches du workflow {workflow.name} sont complétées, statut mis à jour: COMPLETED")

                # Notifier la complétion du workflow via WebSocket
                from websocket_service.client import notify_event
                notify_event('workflow_status_change', {
                    'workflow_id': str(workflow.id),
                    'status': 'COMPLETED',
                    'message': f"Workflow {workflow.name} complété"
                })
            
            elif running==0 and failed > 0:
                # TODO estimer les ressources des taches echouées et demander une liste de volontaire pour cela
                pass

        else:
            logger.warning(f"Aucune assignation trouvée pour la tâche {task.name} et le volontaire {volunteer.name}")
            # Créer une nouvelle assignation complétée
            volunteer_task = VolunteerTask.objects.create(
                task=task,
                volunteer=volunteer,
                assigned_at=timezone.now(),
                started_at=timezone.now(),
                completed_at=timezone.now(),
                status="COMPLETED",
                result=result,
                progress=100.0
            )
            logger.info(f"Nouvelle assignation créée (complétée): tâche {task.name} complétée par le volontaire {volunteer.name}")
        
        # Mettre à jour le statut de la tâche
        task.status = "COMPLETED"
        task.save()
        logger.info(f"Statut de la tâche {task.name} mis à jour: COMPLETED")
        
        # Libérer les ressources du volontaire
        volunteer.status = "available"
        volunteer.save()
        logger.info(f"Volontaire {volunteer.name} marqué comme disponible")
        
        # Vérifier si toutes les tâches du workflow sont complétées
        pending_tasks = workflow.tasks.exclude(status="COMPLETED").count()
        if pending_tasks == 0:
            # Toutes les tâches sont complétées, mettre à jour le statut du workflow
            workflow.status = "COMPLETED"
            workflow.save()
            logger.info(f"Toutes les tâches du workflow {workflow.id} sont complétées, statut mis à jour: COMPLETED")
            
            # Notifier la complétion du workflow via WebSocket
            from websocket_service.client import notify_event
            notify_event('workflow_status_change', {
                'workflow_id': str(workflow.id),
                'status': 'COMPLETED',
                'message': f"Workflow {workflow.name} complété"
            })
        else:
            logger.info(f"Il reste {pending_tasks} tâches en attente pour le workflow {workflow.id}")
        
        # Notifier le changement de statut de la tâche via WebSocket
        from websocket_service.client import notify_event
        notify_event('task_status_change', {
            'workflow_id': str(workflow.id),
            'task_id': str(task.id),
            'status': 'COMPLETED',
            'volunteer': volunteer.name,
            'message': f"Tâche {task.name} complétée par {volunteer.name}"
        })
        
        return True
        
    except Workflow.DoesNotExist:
        logger.error(f"Le workflow {workflow_id} n'existe pas")
    except Task.DoesNotExist:
        logger.error(f"La tâche {task_id} n'existe pas")
    except Volunteer.DoesNotExist:
        logger.error(f"Le volontaire {volunteer_id} n'existe pas")
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la complétion de la tâche: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return False


def listen_for_task_complete():
    """
    Fonction qui écoute le canal de la complétion des tâches
    
    Cette fonction s'abonne au canal 'task/complete' pour recevoir les notifications
    de complétion de tâches par les volontaires.
    
    Returns:
        bool: True si la souscription a réussi, False sinon
    """
    import logging
    from django.utils import timezone
    logger = logging.getLogger(__name__)
    
    try:
        from redis_communication.client import RedisClient
        
        client = RedisClient.get_instance()
        if not 'handle_task_complete' in client.handlers.values():
            logger.info(f"[{timezone.now()}] Souscription au canal 'task/complete'")
            client.subscribe('task/complete', handle_task_complete)
            logger.info(f"[{timezone.now()}] Souscription au canal 'task/complete' réussie")
        
        # Vérifier que le client Redis est bien connecté
        if client.running:
            logger.info(f"[{timezone.now()}] Client Redis connecté avec succès")
        else:
            logger.warning(f"[{timezone.now()}] Client Redis non connecté, les messages ne seront pas reçus")
            return False
            
        return True
    except Exception as e:
        logger.error(f"[{timezone.now()}] Erreur lors de la souscription au canal 'task/complete': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False




def listen_for_task_accept():
    """
    Fonction qui écoute le canal de l'acceptation des tâches
    
    Cette fonction s'abonne au canal 'task/accept' pour recevoir les notifications
    d'acceptation de tâches par les volontaires.
    
    Returns:
        bool: True si la souscription a réussi, False sinon
    """
    import logging
    from django.utils import timezone
    logger = logging.getLogger(__name__)
    
    try:
        from redis_communication.client import RedisClient
        
        client = RedisClient.get_instance()
        if not 'handle_task_accept' in client.handlers.values():
            logger.info(f"[{timezone.now()}] Souscription au canal 'task/progress'")
            client.subscribe('task/progress', handle_task_accept)
            logger.info(f"[{timezone.now()}] Souscription au canal 'task/progress' réussie")
        
        # Vérifier que le client Redis est bien connecté
        if client.running:
            logger.info(f"[{timezone.now()}] Client Redis connecté avec succès")
        else:
            logger.warning(f"[{timezone.now()}] Client Redis non connecté, les messages ne seront pas reçus")
            return False
            
        return True
    except Exception as e:
        logger.error(f"[{timezone.now()}] Erreur lors de la souscription au canal 'task/accept': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False




def listen_task_progress():
    """
    Fonction qui écoute le canal de la progression des tâches
    
    Cette fonction s'abonne au canal 'task/progress' pour recevoir les notifications
    de progression des tâches par les volontaires.
    
    Returns:
        bool: True si la souscription a réussi, False sinon
    """
    import logging
    from django.utils import timezone
    logger = logging.getLogger(__name__)
    
    try:
        from redis_communication.client import RedisClient
        
        client = RedisClient.get_instance()
        if not 'handle_task_progress' in client.handlers.values():
            logger.info(f"[{timezone.now()}] Souscription au canal 'task/progress'")
            client.subscribe('task/progress', handle_task_progress)
            logger.info(f"[{timezone.now()}] Souscription au canal 'task/progress' réussie")
        
        # Vérifier que le client Redis est bien connecté
        if client.running:
            logger.info(f"[{timezone.now()}] Client Redis connecté avec succès")
        else:
            logger.warning(f"[{timezone.now()}] Client Redis non connecté, les messages ne seront pas reçus")
            return False
            
        return True
    except Exception as e:
        logger.error(f"[{timezone.now()}] Erreur lors de la souscription au canal 'task/progress': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False



def listen_for_task_status():
    """
        Gere les status des taches et mets à jour le statut des taches
    Returns:
        bool: True si la souscription a réussi, False sinon
    """
    

    import logging
    from django.utils import timezone
    logger = logging.getLogger(__name__)
    
    try:
        from redis_communication.client import RedisClient
        
        client = RedisClient.get_instance()
        if not 'handle_task_status' in client.handlers.values():
            logger.info(f"[{timezone.now()}] Souscription au canal 'task/status'")
            client.subscribe('task/status', handle_task_status)
            logger.info(f"[{timezone.now()}] Souscription au canal 'task/status' réussie")
        
        # Vérifier que le client Redis est bien connecté
        if client.running:
            logger.info(f"[{timezone.now()}] Client Redis connecté avec succès")
        else:
            logger.warning(f"[{timezone.now()}] Client Redis non connecté, les messages ne seront pas reçus")
            return False
            
        return True
    except Exception as e:
        logger.error(f"[{timezone.now()}] Erreur lors de la souscription au canal 'task/progress': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    