from django.apps import AppConfig
import os
import json
from django.conf import settings
import uuid
import threading
from communication.PubSub.get_redis_instance import get_redis_manager   
import json
import getpass
import hashlib
import time

def generate_static_password_from_username():
    username = getpass.getuser() 
    return username, username

def generate_unique_username():
    """Génère un nom d'utilisateur unique basé sur le nom d'utilisateur système et un timestamp"""
    username = getpass.getuser()
    return username

def handle_login_response(data):
    """
    Gère la réponse de connexion du serveur Redis.
    """
    print(f"[DEBUG] Traitement de la réponse de connexion: {data}")
    
    if not isinstance(data, dict) or "request_id" not in data: 
        print(f"[ERROR] Message recu pas correctement formate: {data}")
        return 
    
    request_id = data.get("request_id")

    # Verifier si la reponse est bien la notre (celle dans le fichier .manager_app/login_request_id.json)
    login_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "login_request_id.json")
    if not os.path.exists(login_request_id_path):
        print("[WARNING] Le fichier login_request_id.json n'existe pas. Peut-être déjà traité.")
        # Vérifier si le message est une réponse de succès, dans ce cas on continue quand même
        if data.get("status") != "success":
            return
    else:
        try:
            with open(login_request_id_path, "r") as f:
                login_request_id = json.load(f).get("request_id")
        except json.JSONDecodeError:
            print(f"[ERROR] Impossible de décoder le fichier JSON {login_request_id_path}")
            return
        
        if request_id != login_request_id:
            print(f"[WARNING] Le request_id de la réponse ne correspond pas à celui notre demande. Attendu: {login_request_id}, Reçu: {request_id}")
            return
        else:
            print(f"[INFO] Le request_id de la réponse correspond à celui de notre demande. Attendu: {login_request_id}, Reçu: {request_id}")

            # Supprimer le fichier login_request_id.json avec gestion des erreurs
            try:
                os.remove(login_request_id_path)
                print(f"[INFO] Le fichier {login_request_id_path} a été supprimé.")
            except FileNotFoundError:
                print(f"[WARNING] Le fichier {login_request_id_path} a déjà été supprimé.")
            except Exception as e:
                print(f"[ERROR] Erreur lors de la suppression du fichier {login_request_id_path}: {e}")
    
    # Traiter la réponse
    status = data.get("status")
    message = data.get("message")
    
    print(f"[INFO] Statut de la réponse de connexion: {status}, Message: {message}")
    
    if status == "success":
        # Extraire les informations d'authentification directement du message
        auth_info = {
            "token": data.get("token"),
            "manager_id": data.get("manager_id"),
            "username": data.get("username"),
            "email": data.get("email"),
            "timestamp": data.get("timestamp")
        }
        
        print(f"[DEBUG] Informations d'authentification extraites: {auth_info}")
        
        # Enregistrer les informations d'authentification dans le fichier .manager_app/manager_auth_info.json
        manager_auth_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_auth_info.json")
        if not os.path.exists(manager_auth_info_path):
            print("[WARNING] Le fichier manager_auth_info.json n'existe pas. Création du fichier.")
            with open(manager_auth_info_path, "w") as f:
                json.dump({}, f)
        
        try:
            with open(manager_auth_info_path, "r") as f:
                existing_auth_info = json.load(f)
            
            # Mettre à jour les informations existantes avec les nouvelles
            existing_auth_info.update(auth_info)
            
            with open(manager_auth_info_path, "w") as f:
                json.dump(existing_auth_info, f)
            
            print(f"[INFO] Informations d'authentification enregistrées dans {manager_auth_info_path}")
        
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'enregistrement des informations d'authentification: {e}")
        
        return
    else:
        print(f"[ERROR] Échec de la connexion avec request_id: {request_id}, message: {message}")

def handle_registration_response(data):
    """
    Gère la réponse d'enregistrement du serveur Redis.
    """
    print(f"[DEBUG] Traitement de la réponse d'enregistrement: {data}")
    
    if not isinstance(data, dict) or "request_id" not in data: 
        print(f"[ERROR] Message recu pas correctement formate, {data}")
        return 
    
    request_id = data.get("request_id")

    # Verifier si la reponse est bien la notre (celle dans le fichier .manager_app/registration_request_id.json)
    registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "registration_request_id.json")
    if not os.path.exists(registration_request_id_path):
        print("[WARNING] Le fichier registration_request_id.json n'existe pas. Peut-être déjà traité.")
        # Vérifier si le message est une réponse de succès, dans ce cas on continue quand même
        if data.get("status") != "success":
            return
    else:
        try:
            with open(registration_request_id_path, "r") as f:
                registration_request_id = json.load(f).get("request_id")
        except json.JSONDecodeError:
            print(f"[ERROR] Impossible de décoder le fichier JSON {registration_request_id_path}")
            return
        
        if request_id != registration_request_id:
            print(f"[WARNING] Le request_id de la réponse ne correspond pas à celui notre demande. Attendu: {registration_request_id}, Reçu: {request_id}")
            return
        else:
            print(f"[INFO] Le request_id de la réponse correspond à celui de notre demande. Attendu: {registration_request_id}, Reçu: {request_id}")

            # Supprimer le fichier registration_request_id.json avec gestion des erreurs
            try:
                os.remove(registration_request_id_path)
                print(f"[INFO] Le fichier {registration_request_id_path} a été supprimé.")
            except FileNotFoundError:
                print(f"[WARNING] Le fichier {registration_request_id_path} a déjà été supprimé.")
            except Exception as e:
                print(f"[ERROR] Erreur lors de la suppression du fichier {registration_request_id_path}: {e}")
    
    # Traiter la réponse
    status = data.get("status")
    message = data.get("message")
    
    print(f"[INFO] Statut de la réponse: {status}, Message: {message}")
    
    if status == "success":
        # Extraire les informations du manager directement du message
        manager_info = {
            "manager_id": data.get("manager_id"),
            "username": data.get("username"),
            "email": data.get("email"),
            "timestamp": data.get("timestamp")
        }
        
        print(f"[DEBUG] Informations du manager extraites: {manager_info}")
        
        # Enregistrer les informations du manager dans le fichier .manager_app/manager_info.json
        manager_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_info.json")
        if not os.path.exists(manager_info_path):
            print("[WARNING] Le fichier manager_info.json n'existe pas. Création du fichier.")
            with open(manager_info_path, "w") as f:
                json.dump({}, f)
        
        try:
            with open(manager_info_path, "r") as f:
                existing_manager_info = json.load(f)
            
            # Mettre à jour les informations existantes avec les nouvelles
            existing_manager_info.update(manager_info)
            
            with open(manager_info_path, "w") as f:
                json.dump(existing_manager_info, f)
            
            print(f"[INFO] Informations du manager enregistrées dans {manager_info_path}: {existing_manager_info}")
            
            # Lancer automatiquement le processus de login après un enregistrement réussi
            print("[INFO] Lancement automatique du processus de login après enregistrement réussi")
            send_login_message()
            
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'enregistrement des informations du manager: {e}")
        
        return
    else:
        print(f"[ERROR] Échec de l'enregistrement avec request_id: {request_id}, message: {message}")
        
        # Si l'erreur est que l'utilisateur existe déjà, on tente une nouvelle inscription avec un nom d'utilisateur unique
        if "déjà utilisé" in message:
            print("[INFO] L'utilisateur existe déjà, tentative d'enregistrement avec un nom d'utilisateur unique...")
            CommunicationConfig.send_registration_message_with_unique_username()
        # Sinon, on tente quand même de se connecter avec les identifiants actuels
        else:
            print("[INFO] Tentative de connexion avec les identifiants actuels...")
            
            # Sauvegarder temporairement le nom d'utilisateur et le mot de passe utilisés pour l'enregistrement
            username, password = generate_static_password_from_username()
            temp_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "temp_credentials.json")
            with open(temp_info_path, "w") as f:
                json.dump({"username": username, "password": password}, f)
            
            # Lancer le processus de login
            send_login_message()

def handle_workflow_submission_response(data):  
    """
    Gère la réponse de soumission de workflow du serveur Redis.
    """
    if not isinstance(data, dict) or "request_id" not in data: 
        print("message recu pas correctement formate")
        return 
    
    request_id = data.get("request_id")

    # Verifier si la reponse est bien la notre  (celle dans le fichier .manager_app/registration_request_id.json)
    workflow_submission_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "workflow_submission_request_id.json")
    if not os.path.exists(workflow_submission_request_id_path):
        print("[ERROR] Le fichier workflow_submission_request_id.json n'existe pas.")
        return
    with open(workflow_submission_request_id_path, "r") as f:
        workflow_submission_request_id = json.load(f).get("request_id")
        workflow_local_id = data.get("info").get("workflow_id")
    if request_id != workflow_submission_request_id:
        print(f"[WARNING] Le request_id de la réponse ne correspond pas à celui notre demande. Attendu: {workflow_submission_request_id}, Reçu: {request_id}")
        return
    else:
        print(f"[INFO] Le request_id de la réponse correspond à celui de notre demande. Attendu: {workflow_submission_request_id}, Reçu: {request_id}")

        # Supprimer le fichier workflow_submission_request_id.json
        os.remove(workflow_submission_request_id_path)
        print(f"[INFO] Le fichier {workflow_submission_request_id_path} a été supprimé.")
    
    # Traiter la réponse
    status = data.get("status")
    message = data.get("message")
    if status == "success":
        # Enregistrer les informations du manager dans le fichier .manager_app/manager_info.json
        manager_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_info.json")
        if not os.path.exists(manager_info_path):
            print("[WARNING] Le fichier manager_info.json n'existe pas. Création du fichier.")
            with open(manager_info_path, "w") as f:
                json.dump({}, f)
        with open(manager_info_path, "r") as f:
            manager_info = json.load(f)
        manager_info.update(data.get("info"))
        with open(manager_info_path, "w") as f:
            json.dump(manager_info, f)
        print(f"[INFO] Informations du manager enregistrées dans {manager_info_path}")
        
        # Enregistrer l'id du workflow dans la base de données
        from workflows.models import Workflow
        workflow_id = data.get("info").get("workflow_id")
        workflow = Workflow.objects.get(workflow_id=workflow_local_id)
        workflow.coordinator_workflow_id = workflow_id
        workflow.status = "SPLITTING"  # Utiliser la constante directement pour éviter l'importation circulaire
        workflow.save()

        # Envoyer l'information au frontend
#         redis_manager = get_redis_manager()
#         message = {
#             "workflow_id": workflow_local_id,
#             "status": "SUBMITTED",
#             "message": f"Le workflow avec l'id {workflow_local_id} a été soumis avec succès.",
#             "results": {}
#         }
#         redis_manager.publish("workflow/status", json.dumps(message))
#         print(f"[INFO] Message de statut de workflow publié sur le canal workflow/status.")

        # Engager l'operation de division du workflow
        from workflows.split_workflow import split_workflow
        return split_workflow(workflow_local_id)
    else:
        print(f"[ERROR] Échec de la soumission de workflow avec request_id: {request_id}, message: {message}")

def handle_task_progress(data):
    """
    Gère la progression des tâches.
    """
    if not isinstance(data, dict):
        print(f"[ERROR] Les données du message ne sont pas au format attendu.")
        return
    task_id = data.get("task_id")
    workflow_id = data.get("workflow_id")
    progress = data.get("progress")
    status = data.get("status")

    # Vérifier si le workflow existe
    from workflows.models import Workflow
    try:
        workflow = Workflow.objects.get(coordinator_workflow_id=workflow_id)
    except Workflow.DoesNotExist:
        print(f"[ERROR] Le workflow avec l'id {workflow_id} n'existe pas.")
        return
    # Mettre à jour la tâche dans la base de données
    task = workflow.tasks.filter(id=task_id).first()
    if not task:
        print(f"[ERROR] La tâche avec l'id {task_id} n'existe pas dans le workflow avec l'id {workflow_id}.")
        return
    # Mettre à jour la tâche dans la base de données
    from tasks.models import Task
    try:
        task.progress = progress
        task.status = Task.STATUS[status] 
        task.save()

        print(f"[INFO] La tâche avec l'id {task_id} a été mise à jour avec succès.")
    except Task.DoesNotExist:
        print(f"[ERROR] La tâche avec l'id {task_id} n'existe pas.")
        return
    except Exception as e:
        print(f"[ERROR] Une erreur s'est produite lors de la mise à jour de la tâche : {e}")
        return
    
    # Envoyer l'information au frontend

def handle_task_finish(data):
    """
    Gère la fin des tâches.
    """
    if not isinstance(data, dict):
        print(f"[ERROR] Les données du message ne sont pas au format attendu.")
        return
    task_id = data.get("task_id")
    status = data.get("status")
    workflow_id = data.get("workflow_id")
    # Vérifier si le workflow existe
    from workflows.models import Workflow, WorkflowType, WorkflowStatus
    try:
        workflow = Workflow.objects.get(coordinator_workflow_id=workflow_id)
    except Workflow.DoesNotExist:
        print(f"[ERROR] Le workflow avec l'id {workflow_id} n'existe pas.")
        return
    # Vérifier si la tâche existe
    task = workflow.tasks.filter(id=task_id).first()
    if not task:
        print(f"[ERROR] La tâche avec l'id {task_id} n'existe pas dans le workflow avec l'id {workflow_id}.")
        return
    
    # Mettre à jour la tâche dans la base de données
    from tasks.models import Task, TaskStatus
    try:
        task.status = TaskStatus[status]
        task.progress = 100
        task.save()
        print(f"[INFO] La tâche avec l'id {task_id} est terminée avec succès.")
    except Task.DoesNotExist:
        print(f"[ERROR] La tâche avec l'id {task_id} n'existe pas.")
        return
    except Exception as e:
        print(f"[ERROR] Une erreur s'est produite lors de la mise à jour de la tâche : {e}")
        return
    
    # Envoyer l'information au frontend

    # Recuperer les resultats de la tache
    results = data.get("task_results")


    if results:
        print(f"[INFO] Résultats de la tâche reçus : {results}")
        
        # Lancer une requete de telechargement des fichier de resultat

        import requests
        host = results.get("host")
        port = results.get("port")
        paths = results.get("paths")
        if not host or not port or not paths:
            print(f"[ERROR] Les informations de résultats ne sont pas complètes.")
            return
        # Envoyer une requête GET pour télécharger les fichiers
        for path in paths:
            url = f"http://{host}:{port}/{path}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    
                    # Enregistrer le fichier
                    workflow_folder = workflow.input_path
                    output_folder = os.path.join(workflow_folder, "outputs")
                    
                    # Creer le dossier de output s'il n'existe pas
                    if not os.path.exists(output_folder):
                        os.makedirs(output_folder)
                        print(f"[INFO] Dossier {output_folder} créé.")
                    
                    # Enregistrer le fichier
                    file_path = os.path.join(output_folder, task_id, path)
                    file_name = os.path.basename(path)
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"[INFO] Fichier téléchargé : {file_name}")
                else:
                    print(f"[ERROR] Échec du téléchargement du fichier : {url}, statut : {response.status_code}")
            except Exception as e:
                print(f"[ERROR] Une erreur s'est produite lors du téléchargement du fichier : {e}")
        
        # Verifier toutes les taches sont terminees
        all_tasks_finished = True
        for task in workflow.tasks.all():
            if task.status != Task.STATUS["FINISHED"]:
                all_tasks_finished = False
                break
        if all_tasks_finished:
            print(f"[INFO] Toutes les tâches sont terminées. Lancement de l'agrégation des résultats.")
            # Envoyer l'information au frontend

            # Lancer l'operation d'aggregation
            from workflows.aggregation.aggregate_results import aggregate_results
            results_dir = os.path.join(workflow_folder, "outputs")
            if workflow.workflow_type == WorkflowType.ML_TRAINING:
                output_model_path = os.path.join(workflow_folder, "outputs", "aggregated_model.pth")
                workflow.status = WorkflowStatus.AGGREGATING
                workflow.save()

                # Envoyer l'information au frontend

                # Lancer l'agrégation
                aggregate_results(results_dir, output_model_path)
            elif workflow.workflow_type == WorkflowType.CUSTOM:
                output_model_path = os.path.join(workflow_folder, "outputs", "inference_results.pkl")
                aggregate_results(results_dir, output_model_path)
            else:
                print(f"[ERROR] Type de workflow non pris en charge pour l'agrégation : {workflow.workflow_type}")
                return
            
            # Mettre à jour le statut du workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.save()
            # Envoyer l'information au frontend


            print(f"[INFO] Le workflow avec l'id {workflow.workflow_id} est terminé.")

            # Publier un message sur le canal de fin de workflow
            redis_manager = get_redis_manager()
            message = {
                "workflow_id": workflow.workflow_id,
                "status": "completed",
                "message": f"Le workflow avec l'id {workflow.workflow_id} est terminé.",
                "results": {
                    "model_path": output_model_path,
                    "results_dir": results_dir
                }
            }
            redis_manager.publish("workflow/finish", json.dumps(message))
            print(f"[INFO] Message de fin de workflow publié sur le canal workflow/finish.")
        else:
            print(f"[INFO] Pas toutes les tâches sont terminées. Attente de la fin des autres tâches.")                      
            # Envoyer l'information au frontend

    else:
        print(f"[WARNING] Aucun résultat de tâche reçu.")

def handle_message(message):
    # Adaptation pour les messages du coordinateur
    # Le coordinateur envoie directement le contenu du message sans structure channel/data
    print(f"[DEBUG] Message reçu: {message}")
    
    # Si le message vient directement de redis-py, il a une structure spécifique
    if isinstance(message, dict) and "type" in message and message["type"] == "message":
        channel = message.get("channel")
        data = message.get("data")
        
        # Si les données sont une chaîne JSON, les parser
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                print(f"[ERROR] Impossible de parser les données JSON: {data}")
                return
        
        # Créer le message formaté
        formatted_message = {
            "channel": channel,
            "data": data
        }
        
        print(f"[INFO] Message formaté depuis redis-py: {formatted_message}")
    else:
        # Traitement pour les autres formats de message
        if not isinstance(message, dict):
            print(f"[WARNING] Message reçu au format non-dict: {message}")
            try:
                # Essayer de parser le message comme JSON si c'est une chaîne
                if isinstance(message, str):
                    message = json.loads(message)
                    print(f"[INFO] Message parsé comme JSON: {message}")
                else:
                    print(f"[ERROR] Format de message non pris en charge: {type(message)}")
                    return
            except json.JSONDecodeError:
                print(f"[ERROR] Impossible de parser le message comme JSON: {message}")
                return

        # Vérifier si le message est au format attendu (avec channel) ou s'il s'agit directement des données
        if "channel" not in message:
            # Déterminer le canal à partir du contexte de la réception
            # Ceci est une solution temporaire, idéalement nous devrions avoir cette information
            if "request_id" in message and "status" in message:
                if "manager_id" in message or message.get("status") == "error":
                    channel = "auth/register_response"
                else:
                    channel = "auth/login_response"
            else:
                print(f"[ERROR] Impossible de déterminer le canal pour le message: {message}")
                return
            
            # Créer la structure attendue
            formatted_message = {
                "channel": channel,
                "data": message
            }
        else:
            formatted_message = message
        
        print(f"[INFO] Message formaté: {formatted_message}")
    
    channel = formatted_message.get("channel")
    data = formatted_message.get("data")
    
    if not channel:
        print(f"[ERROR] Canal manquant dans le message formaté: {formatted_message}")
        return
    
    thread = None

    if channel == "task/progress":
        thread = threading.Thread(target=handle_task_progress, args=(data,))
        thread.start()
        return thread
    elif channel == "task/finish":
        thread = threading.Thread(target=handle_task_finish, args=(data,))
        thread.start()
        return thread
    elif channel == "auth/login_response":
        thread = threading.Thread(target=handle_login_response, args=(data,))
        thread.start()
        return thread
    elif channel == "auth/register_response":
        thread = threading.Thread(target=handle_registration_response, args=(data,))
        thread.start()
        return thread
    elif channel == "WORKFLOW_SUBMISSION_RESPONSE":
        thread = threading.Thread(target=handle_workflow_submission_response, args=(data,))
        thread.start()
        return thread
    elif channel == "WORKFLOW_VOLUNTEER_ASSIGNMENT":
        # Récupérer les informations du workflow et des volontaires
        if not isinstance(message["data"], dict):
            print(f"[ERROR] Les données du message ne sont pas au format attendu.")
            return
        wockflow_id = message['data'].get("workflow_id")
        volunteers = message['data'].get("volunteers")
        # Verifier si le workflow existe
        from workflows.models import Workflow
        try:
            workflow = Workflow.objects.get(workflow_id=wockflow_id)
        except Workflow.DoesNotExist:
            print(f"[ERROR] Le workflow avec l'id {wockflow_id} n'existe pas.")
            return
        if not volunteers:
            print(f"[ERROR] Aucun volontaire n'a été envoyé pour le workflow avec l'id {wockflow_id}.")
            return
        # Appeler la fonction d'affectation de workflow aux volontaires
        from tasks.scheduller import assign_workflow_to_volunteers
        assign_workflow_to_volunteers(workflow, volunteers)
        return thread
    elif channel == "TASK_PROGRESS":
        # Récupérer les informations de progression de la tâche
        if not isinstance(message["data"], dict):
            print(f"[ERROR] Les données du message ne sont pas au format attendu.")
            return
        task_id = message['data'].get("task_id")
        progress = message['data'].get("progress")
        status = message['data'].get("status")
        # Mettre à jour la tâche dans la base de données
        from tasks.models import Task
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            print(f"[ERROR] La tâche avec l'id {task_id} n'existe pas.")
            return
        task.progress = progress
        task.status = status
        task.save()
        return thread
    else:
        print(f"[WARNING] Canal non reconnu : {channel}")
        return None

class CommunicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communication'
    
    # Variable de classe pour suivre si l'initialisation a déjà été effectuée
    _initialized = False

    def ready(self):
        # Éviter d'exécuter cette méthode lors des appels à manage.py autres que runserver
        import sys
        if not 'runserver' in sys.argv:
            return
            
        # Éviter les initialisations multiples
        if CommunicationConfig._initialized:
            print("[INFO] Configuration de communication déjà initialisée.")
            return
            
        CommunicationConfig._initialized = True
        print("[INFO] Initialisation de la configuration de communication...")

        # Créer le dossier .manager_app s'il n'existe pas
        manager_app_path = os.path.join(settings.BASE_DIR, ".manager_app")
        if not os.path.exists(manager_app_path):
            os.makedirs(manager_app_path)
            print(f"[INFO] Dossier {manager_app_path} créé.")

        # Vérifier si les informations du manager existent
        self.check_manager_info()

        # Initialiser le gestionnaire Redis
        try:
            redis_manager = get_redis_manager()
            redis_manager.connect()
            redis_manager.subscribe(handle_message)
            print("[INFO] Connexion Redis établie et souscription aux canaux effectuée.")
        except Exception as e:
            print(f"[ERROR] Impossible d'initialiser le gestionnaire Redis : {e}")

    def check_manager_info(self):
        """
        Vérifie si les informations du manager existent dans le fichier .manager_app/manager_info.json.
        Si elles n'existent pas, envoie un message d'enregistrement au serveur Redis.
        """
        manager_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_info.json")
        
        # Vérifier si un enregistrement est déjà en cours
        registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "registration_request_id.json")
        if os.path.exists(registration_request_id_path):
            print("[INFO] Une demande d'enregistrement est déjà en cours. Suppression du fichier obsolète.")
            try:
                os.remove(registration_request_id_path)
            except Exception as e:
                print(f"[ERROR] Impossible de supprimer le fichier {registration_request_id_path}: {e}")
        
        if not os.path.exists(manager_info_path):
            print("[WARNING] Le fichier manager_info.json n'existe pas. Création du fichier.")
            with open(manager_info_path, "w") as f:
                json.dump({}, f)
            self.send_registration_message()
        else:
            try:
                with open(manager_info_path, "r") as f:
                    manager_info = json.load(f)
                
                if not manager_info.get("manager_id"):
                    print("[WARNING] L'ID du manager n'existe pas. Envoi d'un message d'enregistrement.")
                    self.send_registration_message()
                else:
                    print(f"[INFO] ID du manager : {manager_info.get('manager_id')}")
                    self.send_login_message()
            except json.JSONDecodeError:
                print(f"[ERROR] Le fichier {manager_info_path} est corrompu. Recréation du fichier.")
                with open(manager_info_path, "w") as f:
                    json.dump({}, f)
                self.send_registration_message()
            except Exception as e:
                print(f"[ERROR] Erreur lors de la lecture du fichier {manager_info_path}: {e}")
    
    def send_registration_message(self):
        """
        Envoie un message d'enregistrement au serveur Redis.
        Le message contient le request_id, le nom du manager et l'ID utilisateur.
        """
        try:
            request_id = str(uuid.uuid4())
            registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "registration_request_id.json")
            with open(registration_request_id_path, "w") as f:
                json.dump({"request_id": request_id}, f)
            username, password = generate_static_password_from_username()
            message = {
                "request_id": request_id,
                "username": username, 
                "email": f"{username}@manager_app.com", 
                "password": password,  
                "client_ip": os.getenv("ETHERNET_IP", "127.0.0.1"),  
                "client_info": {
                    "manager_name": os.name,
                    "user_id": os.getuid()
                }
            }
            
            redis_manager = get_redis_manager()
            redis_manager.publish("auth/register", json.dumps(message))
            print(f"[INFO] Message d'enregistrement envoyé avec request_id: {request_id}")
        except Exception as e:
            print(f"[ERROR] Impossible d'envoyer le message d'enregistrement : {e}")

    @staticmethod
    def send_registration_message_with_unique_username():
        """
        Envoie un message d'enregistrement au serveur Redis avec un nom d'utilisateur unique.
        Le message contient le request_id, le nom du manager et l'ID utilisateur.
        """
        try:
            request_id = str(uuid.uuid4())
            registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "registration_request_id.json")
            with open(registration_request_id_path, "w") as f:
                json.dump({"request_id": request_id}, f)
            unique_username = generate_unique_username()
            password = generate_static_password_from_username()[1]
            message = {
                "request_id": request_id,
                "username": unique_username, 
                "email": f"{unique_username}@manager_app.com", 
                "password": password,  
                "client_ip": os.getenv("ETHERNET_IP", "127.0.0.1"),  
                "client_info": {
                    "manager_name": os.name,
                    "user_id": os.getuid()
                }
            }
            
            redis_manager = get_redis_manager()
            redis_manager.publish("auth/register", json.dumps(message))
            print(f"[INFO] Message d'enregistrement envoyé avec request_id: {request_id} et nom d'utilisateur unique: {unique_username}")
        except Exception as e:
            print(f"[ERROR] Impossible d'envoyer le message d'enregistrement : {e}")

    @staticmethod
    def send_login_message():
        """
        Envoie un message de connexion au serveur Redis avec les informations du manager.
        Le message contient le request_id, le username et le password.
        """
        try:
            # Vérifier si des informations temporaires existent (cas où l'utilisateur existe déjà)
            temp_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "temp_credentials.json")
            if os.path.exists(temp_info_path):
                try:
                    with open(temp_info_path, "r") as f:
                        temp_credentials = json.load(f)
                    
                    username = temp_credentials.get("username")
                    password = temp_credentials.get("password")
                    
                    # Supprimer le fichier temporaire après utilisation
                    try:
                        os.remove(temp_info_path)
                        print(f"[INFO] Fichier temporaire {temp_info_path} supprimé après utilisation.")
                    except Exception as e:
                        print(f"[WARNING] Impossible de supprimer le fichier temporaire: {e}")
                    
                    if username and password:
                        print(f"[INFO] Utilisation des informations temporaires pour la connexion: {username}")
                    else:
                        raise ValueError("Informations temporaires incomplètes")
                except Exception as e:
                    print(f"[ERROR] Erreur lors de la lecture des informations temporaires: {e}")
                    # Continuer avec la méthode normale
                    username, password = None, None
            else:
                username, password = None, None
            
            # Si pas d'informations temporaires, utiliser les informations du manager
            if not username or not password:
                # Récupérer les informations du manager
                manager_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_info.json")
                if not os.path.exists(manager_info_path):
                    print("[ERROR] Le fichier manager_info.json n'existe pas. Impossible de se connecter.")
                    return
                
                try:
                    with open(manager_info_path, "r") as f:
                        manager_info = json.load(f)
                    
                    username = manager_info.get("username")
                    if not username:
                        print("[ERROR] Nom d'utilisateur manquant dans manager_info.json")
                        # Utiliser la fonction de génération statique
                        username, password = generate_static_password_from_username()
                        print(f"[INFO] Utilisation du nom d'utilisateur généré: {username}")
                    else:
                        # Utiliser l'ID utilisateur comme mot de passe (comme lors de l'enregistrement)
                        _, password = generate_static_password_from_username()
                    
                except Exception as e:
                    print(f"[ERROR] Erreur lors de la lecture du fichier manager_info.json: {e}")
                    # Utiliser la fonction de génération statique comme fallback
                    username, password = generate_static_password_from_username()
                    print(f"[INFO] Utilisation du nom d'utilisateur généré (fallback): {username}")
            
            # Générer un request_id
            request_id = str(uuid.uuid4())
            login_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "login_request_id.json")
            with open(login_request_id_path, "w") as f:
                json.dump({"request_id": request_id}, f)
            
            # Créer le message
            message = {
                "request_id": request_id,
                "username": username,
                "password": password,
                "client_ip": os.getenv("ETHERNET_IP", "127.0.0.1"),
                "client_info": {
                    "manager_name": os.name,
                    "user_id": os.getuid()
                }
            }
            
            # Envoyer le message
            redis_manager = get_redis_manager()
            redis_manager.publish("auth/login", json.dumps(message))
            print(f"[INFO] Message de connexion envoyé avec request_id: {request_id} pour l'utilisateur {username}")
        except Exception as e:
            print(f"[ERROR] Impossible d'envoyer le message de connexion : {e}")

def send_login_message():
    CommunicationConfig.send_login_message()