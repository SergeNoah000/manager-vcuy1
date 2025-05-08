from django.apps import AppConfig
import os
import json
from django.conf import settings
import uuid
import threading
from communication.PubSub.get_redis_instance import get_redis_manager  



def handle_login_response(data):
    """
    Gère la réponse de connexion du serveur Redis.
    """
    if not isinstance(data, dict) or "request_id" not in data: 
        print("message recu pas correctement formate")
        return 
    
    request_id = data.get("request_id")

    # Verifier si la reponse est bien la notre  (celle dans le fichier .manager_app/login_request_id.json)
    login_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "login_request_id.json")
    if not os.path.exists(login_request_id_path):
        print("[ERROR] Le fichier login_request_id.json n'existe pas.")
        return
    with open(login_request_id_path, "r") as f:
        login_request_id = json.load(f).get("request_id")
    if request_id != login_request_id:
        print(f"[WARNING] Le request_id de la réponse ne correspond pas à celui notre demande. Attendu: {login_request_id}, Reçu: {request_id}")
        return
    else:
        print(f"[INFO] Le request_id de la réponse correspond à celui de notre demande. Attendu: {login_request_id}, Reçu: {request_id}")

        # Supprimer le fichier login_request_id.json
        os.remove(login_request_id_path)
        print(f"[INFO] Le fichier {login_request_id_path} a été supprimé.")
    # Traiter la réponse
    status = data.get("status")
    message = data.get("message")
    if status == "success":
        
        info = data.get("info")

        # Les enregistrer dans le fichier .manager_app/manager_info.json
        manager_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_auth_info.json")
        if not os.path.exists(manager_info_path):
            print("[WARNING] Le fichier manager_auth_info.json n'existe pas. Création du fichier.")
            with open(manager_info_path, "w") as f:
                json.dump({}, f)
        with open(manager_info_path, "r") as f:
            manager_info = json.load(f)
        manager_info.update(info)
        with open(manager_info_path, "w") as f:
            json.dump(manager_info, f)
        print(f"[INFO] Informations du manager enregistrées dans {manager_info_path}")
        return
    else:
        print(f"[ERROR] Échec de la connexion avec request_id: {request_id}, message: {message}")

def handle_registration_response(data):
    """
    Gère la réponse d'enregistrement du serveur Redis.
    """
    if not isinstance(data, dict) or "request_id" not in data: 
        print("message recu pas correctement formate")
        return 
    
    request_id = data.get("request_id")

    # Verifier si la reponse est bien la notre  (celle dans le fichier .manager_app/registration_request_id.json)
    registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "registration_request_id.json")
    if not os.path.exists(registration_request_id_path):
        print("[ERROR] Le fichier registration_request_id.json n'existe pas.")
        return
    with open(registration_request_id_path, "r") as f:
        registration_request_id = json.load(f).get("request_id")
    if request_id != registration_request_id:
        print(f"[WARNING] Le request_id de la réponse ne correspond pas à celui notre demande. Attendu: {registration_request_id}, Reçu: {request_id}")
        return
    else:
        print(f"[INFO] Le request_id de la réponse correspond à celui de notre demande. Attendu: {registration_request_id}, Reçu: {request_id}")

        # Supprimer le fichier registration_request_id.json
        os.remove(registration_request_id_path)
        print(f"[INFO] Le fichier {registration_request_id_path} a été supprimé.")
    
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
             
        return
    else:
        print(f"[ERROR] Échec de l'enregistrement avec request_id: {request_id}, message: {message}")

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
        

        # Engager l'operation de division du workflow
        from workflows.split_workflow import split_workflow
        return split_workflow(workflow_local_id)
    else:
        print(f"[ERROR] Échec de la soumission de workflow avec request_id: {request_id}, message: {message}")

def handle_message(message):
    if not isinstance(message, dict) or "channel" not in message: 
        print("message recu pas correctement formate")
        return 
    
    channel = message.get("channel")
    thread = None

    # Handle responses in a separate thread

    if channel == "LOGIN_RESPONSE":
        thread = threading.Thread(target=handle_login_response, args=(message["data"],))
        thread.start()
        return thread
    elif channel == "MANAGER_REGISTRATION_RESPONSE":
        thread = threading.Thread(target=handle_registration_response, args=(message["data"],))
        thread.start()
        return thread
    elif channel == "WORKFLOW_SUBMISSION_RESPONSE":
        thread = threading.Thread(target=handle_workflow_submission_response, args=(message["data"],))
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

    def ready(self):
        # Éviter d'exécuter cette méthode lors des appels à manage.py
        import sys
        if 'runserver' not in sys.argv:
            return

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
        if not os.path.exists(manager_info_path):
            print("[WARNING] Le fichier manager_info.json n'existe pas. Création du fichier.")
            with open(manager_info_path, "w") as f:
                json.dump({}, f)
            self.send_registration_message()
        else:
            with open(manager_info_path, "r") as f:
                manager_info = json.load(f)
            if not manager_info.get("manager_id"):
                print("[WARNING] L'ID du manager n'existe pas. Envoi d'un message d'enregistrement.")
                self.send_registration_message()
            else:
                print(f"[INFO] ID du manager : {manager_info.get('manager_id')}")
                self.send_login_message()

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
            
            message = {
                "request_id": request_id,
                "manager_name": "Manager Backend",
                "user_id": "admin"
            }
            
            redis_manager = get_redis_manager()
            redis_manager.publish("MANAGER_REGISTRATION", json.dumps(message))
            print(f"[INFO] Message d'enregistrement envoyé avec request_id: {request_id}")
        except Exception as e:
            print(f"[ERROR] Impossible d'envoyer le message d'enregistrement : {e}")

    def send_login_message(self):
        """
        Envoie un message de connexion au serveur Redis avec les informations du manager.
        Le message contient le request_id, le mananger_id et l'ID utilisateur.
        """
        try:
            # Récupérer l'ID du manager
            manager_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_info.json")
            with open(manager_info_path, "r") as f:
                manager_info = json.load(f)
            manager_id = manager_info.get("manager_id")
            
            # Générer un request_id
            request_id = str(uuid.uuid4())
            login_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "login_request_id.json")
            with open(login_request_id_path, "w") as f:
                json.dump({"request_id": request_id}, f)
            
            # Créer le message
            message = {
                "request_id": request_id,
                "manager_id": manager_id,
                "user_id": "admin"
            }
            
            # Envoyer le message
            redis_manager = get_redis_manager()
            redis_manager.publish("LOGIN", json.dumps(message))
            print(f"[INFO] Message de connexion envoyé avec request_id: {request_id}")
        except Exception as e:
            print(f"[ERROR] Impossible d'envoyer le message de connexion : {e}")