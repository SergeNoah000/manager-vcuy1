from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission, Group
from django.utils.translation import gettext_lazy as _
import uuid

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username=None, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        if username is None:
            username = email.split('@')[0]
        return self._create_user(email, password, username=username, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('username', email.split('@')[0])

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with email as the unique identifier."""

    # Ajouter un ID comme clé primaire
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Rendre l'username non unique pour éviter les conflits
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        unique=False,  # Important: permettre des noms d'utilisateur non uniques
    )
    
    # Configurer l'email comme identifiant unique
    email = models.EmailField(_('email address'), unique=True)
    
    # Ajout des related_name pour éviter les conflits
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='workflow_user_set',
        related_query_name='workflow_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='workflow_user_set',
        related_query_name='workflow_user',
    )
    
    # Configurer l'email comme champ de connexion
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # L'username sera défini automatiquement si non fourni
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        swappable = 'AUTH_USER_MODEL'


def get_default_owner():
    """Retourne l'ID de l'utilisateur par défaut."""
    # Utiliser la méthode create_user du gestionnaire pour s'assurer
    # que le mot de passe est correctement haché
    default_user, created = User.objects.get_or_create(
        email='workflow_manager@system.local',
        defaults={
            'username': 'workflow_manager',
            'is_staff': True,
            'password': 'workflow_manager'  # Sera automatiquement haché par create_user
        }
    )
    
    # Si l'utilisateur existait déjà mais que le mot de passe n'était pas défini
    if not created and not default_user.has_usable_password():
        default_user.set_password('workflow_manager')
        default_user.save()
        
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
    
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    max_execution_time = models.IntegerField(default=3600)
    retry_count = models.IntegerField(default=3)
    
    # Nouveaux champs
    executable_path = models.CharField(max_length=500, blank=True, help_text="Chemin vers l'exécutable")
    input_path = models.CharField(max_length=500, blank=True, help_text="Chemin des données d'entrée")
    input_data_size = models.IntegerField(default=0, help_text="Taille des données d'entrée en Mo")
    output_path = models.CharField(max_length=500, blank=True, help_text="Chemin où stocker les résultats")
    
    estimated_resources = models.JSONField(default=dict, blank=True, help_text="Ressources estimées pour le workflow (ex. RAM, CPU...)")
    
    preferences = models.JSONField(default=dict, blank=True, help_text="Critères souhaités pour les volontaires (type de volontaire, ressources disponibles...)")
    workflow_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="Identifiant unique du workflow")
    coordinator_workflow_id = models.UUIDField(null=True, blank=True, unique=True, help_text="Identifiant du workflow venant du coordinnateur du système")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Workflow'
        verbose_name_plural = 'Workflows'