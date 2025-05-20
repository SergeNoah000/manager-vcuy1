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
            'status',
        ]
        read_only_fields = ['id', 'registration_date', 'last_login']

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
        
        # Créer le manager avec les informations système
        manager = Manager.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,  # Stocker temporairement pour la communication
        )
        
        return manager
