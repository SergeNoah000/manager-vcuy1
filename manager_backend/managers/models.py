from django.db import models
import uuid
from django.utils import timezone

# Status constants
STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'
STATUS_SUSPENDED = 'suspended'

class Manager(models.Model):
    """
    Modèle pour les managers dans le système de calcul distribué.
    Version Django ORM du modèle Manager du coordinateur.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.CharField(max_length=255, unique=True)  # Utiliser CharField au lieu de EmailField pour accepter tous les formats d'email
    password = models.CharField(max_length=256, blank=True)  # Stocké uniquement pour la communication, pas pour l'authentification
    registration_date = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20, 
        choices=[
            (STATUS_ACTIVE, 'Actif'),
            (STATUS_INACTIVE, 'Inactif'),
            (STATUS_SUSPENDED, 'Suspendu')
        ],
        default=STATUS_INACTIVE
    )
    coordinator_manager_id = models.UUIDField(null=True, blank=True, help_text="ID du manager dans le système coordinateur")
    
    def __str__(self):
        return f"{self.username} - {self.email} ({self.status})"
    
    class Meta:
        verbose_name = "Manager"
        verbose_name_plural = "Managers"
        ordering = ['-registration_date']

# --- Enums sous forme de constantes (pour la compatibilité avec le coordinateur) ---
WORKFLOW_TYPE_CHOICES = (
    ('DATA_PROCESSING', 'Traitement de données'),
    ('SCIENTIFIC_COMPUTING', 'Calcul scientifique'),
    ('RENDERING', 'Rendu graphique'),
    ('MACHINE_LEARNING', 'Apprentissage automatique'),
)

WORKFLOW_STATUS_CHOICES = (
    ('CREATED', 'Créé'),
    ('VALIDATED', 'Validé'),
    ('SUBMITTED', 'Soumis'),
    ('SPLITTING', 'En découpage'),
    ('ASSIGNING', 'En attribution'),
    ('PENDING', 'En attente'),
    ('RUNNING', 'En exécution'),
    ('PAUSED', 'En pause'),
    ('PARTIAL_FAILURE', 'Échec partiel'),
    ('REASSIGNING', 'Réattribution'),
    ('AGGREGATING', 'Agrégation'),
    ('COMPLETED', 'Terminé'),
    ('FAILED', 'Échoué'),
)

TASK_STATUS_CHOICES = (
    ('PENDING', 'En attente'),
    ('ASSIGNED', 'Assigné'),
    ('RUNNING', 'En exécution'),
    ('PAUSED', 'En pause'),
    ('COMPLETED', 'Terminé'),
    ('FAILED', 'Échoué'),
)
