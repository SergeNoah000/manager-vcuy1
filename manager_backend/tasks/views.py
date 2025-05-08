from django.shortcuts import render, get_object_or_404
from .models import Task
from workflows.models import Workflow

def tasks_by_workflow(request, workflow_id):
    """Affiche toutes les tâches liées à un workflow spécifique."""
    workflow = get_object_or_404(Workflow, id=workflow_id)
    tasks = workflow.tasks.all()
    return render(request, 'tasks/tasks_by_workflow.html', {
        'workflow': workflow,
        'tasks': tasks,
    })

def task_detail(request, task_id):
    """Affiche les détails d'une tâche spécifique."""
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'tasks/task_detail.html', {
        'task': task,
    })

# Placeholder pour tâches par volontaire
def tasks_by_volunteer(request, volunteer_id):
    """(À venir) Affiche les tâches assignées à un volontaire spécifique."""
    # À compléter quand le modèle Volunteer <-> Task est établi
    return render(request, 'tasks/tasks_by_volunteer.html', {
        'volunteer_id': volunteer_id,
        'tasks': [],  # temporairement vide
    })
