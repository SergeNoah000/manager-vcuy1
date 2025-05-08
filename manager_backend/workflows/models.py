from django.db import models
from django.contrib.auth.models import User
import uuid


def get_default_owner():
    default_user, _ = User.objects.get_or_create(
        username='workflow_manager',
        defaults={
            'email': 'workflow_manager@system.local',
            'is_staff': True
        }
    )
    return default_user.id 


class WorkflowType(models.TextChoices):
    MATRIX_ADDITION = 'MATRIX_ADDITION', 'Addition de matrices de grande taille'
    MATRIX_MULTIPLICATION = 'MATRIX_MULTIPLICATION', 'Multiplication de matrices de grande taille'
    ML_TRAINING = 'ML_TRAINING', 'Entraînement de modèle machine learning'
    CUSTOM = 'CUSTOM', 'Workflow personnalisé'


class WorkflowStatus(models.TextChoices):
    CREATED = 'CREATED', 'Créé'
    VALIDATED = 'VALIDATED', 'Validé'
    SUBMITTED = 'SUBMITTED', 'Soumis'
    SPLITTING = 'SPLITTING', 'En découpage'
    ASSIGNING = 'ASSIGNING', 'En attribution'
    PENDING = 'PENDING', 'En attente'
    RUNNING = 'RUNNING', 'En exécution'
    PAUSED = 'PAUSED', 'En pause'
    PARTIAL_FAILURE = 'PARTIAL_FAILURE', 'Échec partiel'
    REASSIGNING = 'REASSIGNING', 'Réattribution'
    AGGREGATING = 'AGGREGATING', 'Agrégation'
    COMPLETED = 'COMPLETED', 'Terminé'
    FAILED = 'FAILED', 'Échoué'


class Workflow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    workflow_type = models.CharField(
        max_length=30, 
        choices=WorkflowType.choices,
        default=WorkflowType.MATRIX_ADDITION
    )

    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        default=get_default_owner
    )

    status = models.CharField(
        max_length=20, 
        choices=WorkflowStatus.choices, 
        default=WorkflowStatus.CREATED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    priority = models.IntegerField(default=1)

    estimated_resources = models.JSONField(default=dict)
    tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)

    max_execution_time = models.IntegerField(default=3600)
    retry_count = models.IntegerField(default=3)

    # Nouveaux champs
    executable_path = models.CharField(max_length=500, blank=True, help_text="Chemin vers l'exécutable")
    input_path = models.CharField(max_length=500, blank=True, help_text="Chemin des données d'entrée")
    input_data_size = models.IntegerField(default=0, help_text="Taille des données d'entrée en Mo")
    output_path = models.CharField(max_length=500, blank=True, help_text="Chemin où stocker les résultats")


    estimated_resources = models.JSONField(default=dict, help_text="Ressources estimées pour le workflow (ex. RAM, CPU...)")
    
    preferences = models.JSONField(default=dict, help_text="Critères souhaités pour les volontaires (type de volontaire, ressources disponibles...)")
    workflow_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="Identifiant unique du workflow")
    coordinator_workflow_id = models.UUIDField(null=True, blank=True, unique=True, help_text="Identifiant du workflow venant du coordinnateur du système")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Workflow'
        verbose_name_plural = 'Workflows'
