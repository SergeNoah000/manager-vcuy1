from tasks.models import Task, TaskStatus
from workflows.models import Workflow, WorkflowStatus
from volunteers.models import Volunteer, VolunteerTask
from django.utils import timezone
from collections import defaultdict


def assign_tasks_fcfs(workflow: Workflow, volunteers_data: list):
    """
    Assigne les tâches d'un workflow aux volontaires selon FCFS,
    tout en vérifiant la disponibilité des ressources de chaque volontaire.
    """

    # Créer ou mettre à jour les volontaires
    volunteer_objs = []
    for vdata in volunteers_data:
        v, _ = Volunteer.objects.update_or_create(
            coordinator_volunteer_id=vdata.get("id"),
            defaults={
                "name": vdata["name"],
                "cpu_cores": vdata["cpu_cores"],
                "ram_mb": vdata["ram_mb"],
                "disk_gb": vdata["disk_gb"],
                "status": "available"
            }
        )
        volunteer_objs.append(v)

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
    tasks = workflow.tasks.filter(status=TaskStatus.PENDING).order_by('created_at')

    task_assignments = defaultdict(list)

    for task in tasks:
        required = task.required_resources

        # Parcourir les volontaires dans l’ordre FCFS
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
        print(f"👤 {volunteer_name} → {len(tasks)} tâche(s): {', '.join(tasks)}")

    # Affichage des tâches non assignées
    unassigned = tasks.exclude(status=TaskStatus.ASSIGNED)
    if unassigned.exists():
        print("\n⚠️  Tâches non assignées :")
        for t in unassigned:
            print(f"  - {t.name} (ressources requises : {t.required_resources})")
    else:
        print("\n✅ Toutes les tâches ont été assignées.")

def assign_workflow_to_volunteers(workflow_instance, volunteers):
    """
    Assigne un workflow à une liste de volontaires.
    """

    # La methode d'assignation des tâches par défaut est FCFS
    return assign_tasks_fcfs(workflow_instance, volunteers)
    
    
    