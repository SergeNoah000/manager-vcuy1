from tasks.models import Task, TaskStatus
from workflows.models import Workflow, WorkflowStatus
from volunteers.models import Volunteer, VolunteerTask
from django.utils import timezone
from collections import defaultdict


def assign_tasks_fcfs(workflow_id: str) -> dict:
    """
    Assigne les tâches d'un workflow aux volontaires selon FCFS,
    tout en vérifiant la disponibilité des ressources de chaque volontaire.
    """
    # Récupérer le workflow
    workflow = Workflow.objects.get(id=workflow_id)
    
    # Récupérer les volontaires disponibles
    volunteers = Volunteer.objects.filter(status="available")
    
    # Initialiser le pool de ressources disponibles pour chaque volontaire
    volunteer_resources = {
        v.id: {
            "volunteer": v,
            "available_cpu": v.cpu_cores,
            "available_ram": v.ram_mb,
            "available_disk": v.disk_gb,
        }
        for v in volunteers
    }

    # Récupérer les tâches en attente
    tasks = workflow.tasks.filter(status=TaskStatus.PENDING).order_by('created_at')

    task_assignments = defaultdict(list)

    for task in tasks:
        required = task.required_resources

        # Parcourir les volontaires dans l'ordre FCFS
        for v_id, res in volunteer_resources.items():
            if (
                res["available_cpu"] >= required.get("cpu_cores", 0) and
                res["available_ram"] >= required.get("ram_mb", 0) and
                res["available_disk"] >= required.get("disk_gb", 0)
            ):
                # Attribuer la tâche à ce volontaire
                VolunteerTask.objects.create(
                    volunteer=res["volunteer"],
                    task=task,
                    assigned_at=timezone.now(),
                    status=TaskStatus.ASSIGNED
                )

                # Réduire les ressources disponibles
                res["available_cpu"] -= required.get("cpu_cores", 0)
                res["available_ram"] -= required.get("ram_mb", 0)
                res["available_disk"] -= required.get("disk_gb", 0)

                # Mettre à jour les statuts
                task.status = TaskStatus.ASSIGNED
                task.save()

                task_assignments[res["volunteer"].name].append(task.name)

                break  # passer à la tâche suivante

    # Marquer les volontaires comme busy si leurs ressources sont épuisées
    for res in volunteer_resources.values():
        volunteer = Volunteer.objects.get(id=res["volunteer"].id)
        if (
            res["available_cpu"] == 0 or
            res["available_ram"] == 0 or
            res["available_disk"] == 0
        ):
            volunteer.status = "busy"
            volunteer.save()

    # Mettre à jour le statut du workflow
    if workflow.tasks.filter(status=TaskStatus.ASSIGNED).exists():
        workflow.status = WorkflowStatus.IN_PROGRESS
        workflow.save()

    # Affichage de la répartition finale
    print("\n=== Répartition des tâches (FCFS) ===")
    for volunteer_name, tasks in task_assignments.items():
        print(f"\U0001F464 {volunteer_name} \u2192 {len(tasks)} tâche(s): {', '.join(tasks)}")

    # Affichage des tâches non assignées
    unassigned = tasks.exclude(status=TaskStatus.ASSIGNED)
    if unassigned.exists():
        print("\n\u26A0\uFE0F  Tâches non assignées :")
        for t in unassigned:
            print(f"  - {t.name} (ressources requises : {t.required_resources})")
    else:
        print("\n\u2705 Toutes les tâches ont été assignées.")
    
    return dict(task_assignments)


def assign_workflow_to_volunteers(workflow: Workflow, volunteers_data: list) -> dict:
    """
    Assigne les tâches d'un workflow aux volontaires selon les données fournies.
    
    Args:
        workflow: L'instance du workflow à assigner
        volunteers_data: Liste des données des volontaires disponibles
        
    Returns:
        Un dictionnaire contenant les assignations de tâches par volontaire
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Début de l'assignation du workflow {workflow.id} aux volontaires")
    logger.warning(f"Nombre de volontaires disponibles: {volunteers_data}")
    
    # Créer ou mettre à jour les volontaires
    volunteer_objs = []
    for vdata in volunteers_data:
        try:
            # Récupérer l'ID du volontaire (clé 'volunteer_id' dans les données du coordinateur)
            volunteer_id = vdata.get("volunteer_id")
            if not volunteer_id:
                logger.error(f"Données de volontaire sans ID: {vdata}")
                continue
                
            # Récupérer les ressources
            resources = vdata.get("resources")
            
            v, created = Volunteer.objects.update_or_create(
                coordinator_volunteer_id=volunteer_id,
                defaults={
                    "name": vdata.get("username", f"Volontaire {volunteer_id}"),
                    "cpu_cores": resources.get("cpu_cores", 1),
                    "ram_mb": resources.get("memory_mb", 1024),
                    "disk_gb": int(resources.get("disk_space_mb", 10240) / 1024),  # Convertir MB en GB
                    "status": "available"
                }
            )
            volunteer_objs.append(v)
            logger.info(f"Volontaire {'créé' if created else 'mis à jour'}: {v.name} (ID: {v.coordinator_volunteer_id})")
        except Exception as e:
            logger.error(f"Erreur lors de la création/mise à jour du volontaire {volunteer_id}: {e}")
            continue
    
    # Initialiser le pool de ressources disponibles pour chaque volontaire
    volunteer_resources = {
        v.id: {
            "volunteer": v,
            "available_cpu": v.cpu_cores,
            "available_ram": v.ram_mb,
            "available_disk": v.disk_gb,
        }
        for v in volunteer_objs
    }
    
    # Récupérer les tâches en attente
    tasks = workflow.tasks.filter(status=TaskStatus.CREATED).order_by('created_at')
    logger.info(f"Nombre de tâches en attente: {tasks.count()}")
    
    task_assignments = defaultdict(list)
    
    for task in tasks:
        required = task.required_resources
        logger.debug(f"Traitement de la tâche {task.name} (ressources requises: {required})")
        
        # Extraire les ressources requises avec les bonnes clés
        required_cpu = required.get("cpu", required.get("cpu_cores", 1))
        required_ram = required.get("ram", required.get("ram_mb", 512))
        required_disk = required.get("disk", required.get("disk_gb", 1))
        
        logger.info(f"Ressources requises normalisées - CPU: {required_cpu}, RAM: {required_ram} MB, Disk: {required_disk} GB")
        
        # Parcourir les volontaires dans l'ordre FCFS
        assigned = False
        for v_id, res in volunteer_resources.items():
            logger.info(f"Vérification des ressources du volontaire {res['volunteer'].name} - CPU: {res['available_cpu']}, RAM: {res['available_ram']}, Disk: {res['available_disk']}")
            if (
                res["available_cpu"] >= required_cpu and
                res["available_ram"] >= required_ram and
                res["available_disk"] >= required_disk
            ):
                # Attribuer la tâche à ce volontaire
                volunteer_task = VolunteerTask.objects.create(
                    volunteer=res["volunteer"],
                    task=task,
                    assigned_at=timezone.now(),
                    status="ASSIGNED"
                )
                logger.info(f"Tâche {task.name} assignée au volontaire {res['volunteer'].name}")
                
                # Réduire les ressources disponibles
                res["available_cpu"] -= required.get("cpu_cores", 0)
                res["available_ram"] -= required.get("ram_mb", 0)
                res["available_disk"] -= required.get("disk_gb", 0)
                
                # Mettre à jour les statuts
                task.status = TaskStatus.ASSIGNED
                task.save()
                
                task_assignments[res["volunteer"].coordinator_volunteer_id].append({
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "assignment_id": str(volunteer_task.id)
                })
                
                assigned = True
                break  # passer à la tâche suivante
        
        if not assigned:
            logger.warning(f"Impossible d'assigner la tâche {task.name}: ressources insuffisantes")
    
    # Marquer les volontaires comme busy si leurs ressources sont épuisées
    for res in volunteer_resources.values():
        volunteer = res["volunteer"]
        if (
            res["available_cpu"] == 0 or
            res["available_ram"] == 0 or
            res["available_disk"] == 0
        ):
            volunteer.status = "busy"
            volunteer.save()
            logger.info(f"Volontaire {volunteer.name} marqué comme occupé")
    
    # Mettre à jour le statut du workflow
    assigned_count = workflow.tasks.filter(status=TaskStatus.ASSIGNED).count()
    if assigned_count > 0:
        workflow.status = WorkflowStatus.PENDING
        workflow.save()
        logger.info(f"Workflow {workflow.id} mis à jour avec le statut PENDING")
    
    # Résumé des assignations
    logger.warning(f"Résumé des assignations: {len(task_assignments)} volontaires, {assigned_count}/{tasks.count()} tâches assignées")
    
    return dict(task_assignments)

# Fonction utilitaire pour créer un handler de tâches
def create_task_handler(task_id: str, volunteer_id: str):
    """
    Crée un handler pour une tâche assignée à un volontaire.
    
    Args:
        task_id: ID de la tâche
        volunteer_id: ID du volontaire
        
    Returns:
        Un dictionnaire contenant les informations du handler
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from tasks.models import Task
        from volunteers.models import Volunteer, VolunteerTask
        
        task = Task.objects.get(id=task_id)
        volunteer = Volunteer.objects.get(coordinator_volunteer_id=volunteer_id)
        
        # Créer l'assignation
        volunteer_task = VolunteerTask.objects.create(
            volunteer=volunteer,
            task=task,
            assigned_at=timezone.now(),
            status="ASSIGNED"
        )
        
        logger.info(f"Tâche {task.name} assignée au volontaire {volunteer.name}")
        
        return {
            "task_id": str(task.id),
            "volunteer_id": str(volunteer.id),
            "assignment_id": str(volunteer_task.id),
            "status": "ASSIGNED"
        }
    except Exception as e:
        logger.error(f"Erreur lors de la création du handler pour la tâche {task_id} et le volontaire {volunteer_id}: {e}")
        return None
    
    
    