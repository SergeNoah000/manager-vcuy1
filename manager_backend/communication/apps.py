from django.apps import AppConfig
import os
import json
from django.conf import settings
import uuid
from django.apps import AppConfig
import threading
from tasks.scheduller import assign_workflow_to_volunteers
from workflows.split_workflow import split_workflow
from workflows.models import Workflow
from communication.PubSub.get_redis_instance import get_redis_manager  



def handle_login_response(data):
    """
    Gère la réponse de connexion du serveur Redis.
    """
    if not isinstance(dict, data) or not "request_id" in data : 
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
    if not isinstance(dict, data) or not "request_id" in data : 
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
    if not isinstance(dict, data) or not "request_id" in data : 
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
        workflow_id = data.get("info").get("workflow_id")
        workflow = Workflow.objects.get(workflow_id=workflow_local_id)
        workflow.coordinator_workflow_id = workflow_id
        workflow.status = Workflow.WorkflowStatus.SPLITTING
        workflow.save()

        # Envoyer l'information au frontend
        

        # Engager l'operation de division du workflow

        return split_workflow(workflow_local_id)
    else:
        print(f"[ERROR] Échec de la soumission de workflow avec request_id: {request_id}, message: {message}")

        




    
def handle_message(message):
    if not isinstance(dict, message) or not "channel" in message : 
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
        # Traiter l'affectation de workflow aux volontaires
        print(f"[INFO] Affectation de workflow aux volontaires: {message['data']}")
        # recuperer les donnees du message (workflow_id, volunteers)
        wockflow_id = message['data'].get("workflow_id")
        volunteers = message['data'].get("volunteers")
        # Verifier si le workflow existe
        try:
            workflow = Workflow.objects.get(workflow_id=wockflow_id)
        except Workflow.DoesNotExist:
            print(f"[ERROR] Le workflow avec l'id {wockflow_id} n'existe pas.")
            return
        # Verifier si les volontaires existent
        if not volunteers:
            print(f"[ERROR] Aucun volontaire n'a été envoyé pour le workflow avec l'id {wockflow_id}.")
            return
        # Appeler la fonction d'affectation de workflow aux volontaires
        assign_workflow_to_volunteers(workflow, volunteers)
        return thread
    elif channel == "TASK_PROGRESS":
         # Appeler la fonction de mise à jour du progrès de la tâche
        print(f"[INFO] Mise à jour du progrès de la tâche: {message['data']}")

        # Verifier que nous sommes le manager du workflow de la tache

    else :
        print("canal non reconu")

    return 


class CommunicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communication'

    def ready(self):
        # Initialisation de Redis
        redis_manager = get_redis_manager()
        redis_manager.subscribe(handle_message)
        pubsub = redis_manager.pubsub()
        pubsub.run_in_thread(sleep_time=0.001)
        
        # creer une autre fonction qui verifi si le fichie manager_info.json du dossier .manager_app du personnel
        # existe et si il est bien formate
        # si oui, on enregistre envoir un message de d'enregistrement dans MANAGER_REGISTRATION avec un request_id
        # et le nom d'hote et son userid 
        # sinon on envoie un message d'erreur
        self.check_manager_info()

    def check_manager_info(self):
        # Chemin vers le fichier manager_info.json
        manager_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_info.json")

        # Vérifier si le fichier existe
        if not os.path.exists(manager_info_path):
            print("[ERROR] Le fichier manager_info.json n'existe pas.")
            
            # appeler la fonction d'envoie du message d'enregistrement
            self.send_registration_message()
            return

        # Vérifier si le fichier est bien formaté en JSON
        try:
            with open(manager_info_path, "r") as f:
                manager_info = json.load(f)
        except json.JSONDecodeError:
            print("[ERROR] Le fichier manager_info.json n'est pas bien formaté.")
            return

        # Envoyer un message de connexion
        self.send_login_message()


    def send_registration_message(self):
        # Récupérer les informations nécessaires
        request_id = str(uuid.uuid4())
        host_name = os.uname()[1]
        user_id = os.getuid()
        
        # Créer le message
        message = {
            "channel": "MANAGER_REGISTRATION",
            "data": {
                "request_id": request_id,
                "host_name": host_name,
                "user_id": user_id
            }
        }
        # Publier le message
        redis_manager = get_redis_manager()
        redis_manager.publish("MANAGER_REGISTRATION", json.dumps(message))
        print(f"[INFO] Message d'enregistrement envoyé avec request_id: {request_id}")
        
        # Enregistrer request_id dans le fichier .manager_app/registration_request_id.json
        registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "registration_request_id.json")
        with open(registration_request_id_path, "w") as f:
            json.dump({"request_id": request_id}, f)
        print(f"[INFO] request_id enregistré dans {registration_request_id_path}")


    
    def send_login_message(self):
        """ 
        Envoie un message de connexion au serveur Redis avec les informations du manager.
        Le message contient le request_id, le mananger_id et l'ID utilisateur.
        """
        # Récupérer les informations nécessaires
        request_id = str(uuid.uuid4())
        manager_id = None
        # Vérifier si le fichier manager_info.json existe
        manager_info_path = os.path.join(settings.BASE_DIR, ".manager_app", "manager_info.json")
        if os.path.exists(manager_info_path):
            with open(manager_info_path, "r") as f:
                manager_info = json.load(f)
                manager_id = manager_info.get("manager_id")
        if not manager_id:
            print("[ERROR] Le manager_id n'est pas trouvé dans le fichier manager_info.json.")
            return self.send_registration_message()
        user_id = os.getuid()
        
        # Créer le message
        message = {
            "channel": "MANAGER_LOGIN",
            "data": {
                "request_id": request_id,
                "manager_id": manager_id,
                "user_id": user_id
            }
        }
        
        # Publier le message
        redis_manager = get_redis_manager()
        redis_manager.publish("MANAGER_LOGIN", json.dumps(message))
        print(f"[INFO] Message de connexion envoyé avec request_id: {request_id}")
        
        # Enregistrer request_id dans le fichier .manager_app/registration_request_id.json
        registration_request_id_path = os.path.join(settings.BASE_DIR, ".manager_app", "login_request_id.json")
        with open(registration_request_id_path, "w") as f:
            json.dump({"request_id": request_id}, f)
        print(f"[INFO] request_id enregistré dans {registration_request_id_path}")

        