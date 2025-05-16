from rest_framework import serializers
from .models import Manager
import socket
import platform
import psutil
import os
from django.utils import timezone

class ManagerSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Manager.
    """
    class Meta:
        model = Manager
        fields = [
            'id', 'username', 'email', 'registration_date', 'last_login', 
            'status', 'coordinator_manager_id', 'system_info'
        ]
        read_only_fields = ['id', 'registration_date', 'last_login', 'coordinator_manager_id']

class ManagerRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'enregistrement d'un nouveau manager.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.CharField(required=True, allow_blank=False)
    
    class Meta:
        model = Manager
        fields = ['username', 'email', 'password']
    
    def create(self, validated_data):
        """
        Surcharge de la méthode create pour ajouter automatiquement les informations système.
        """
        # Récupérer le mot de passe pour le stocker temporairement (pour la communication avec le coordinateur)
        password = validated_data.get('password')
        
        # Collecter les informations système
        system_info = {
            'manager_name': platform.system().lower(),  # 'posix', 'windows', etc.
            'user_id': os.getuid(),
            'hostname': socket.gethostname(),
            'ip_address': socket.gethostbyname(socket.gethostname()),
            'cpu_cores': psutil.cpu_count(logical=True),
            'ram_mb': int(psutil.virtual_memory().total / (1024 * 1024)),
            'disk_gb': int(psutil.disk_usage('/').total / (1024 * 1024 * 1024)),
            'os': platform.system(),
            'os_version': platform.version(),
            'python_version': platform.python_version()
        }
        
        # Créer le manager avec les informations système
        manager = Manager.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,  # Stocker temporairement pour la communication
            system_info=system_info
        )
        
        return manager
