# backend/workflows/serializers.py
from rest_framework import serializers
from .models import Workflow, User
from django.contrib.auth.password_validation import validate_password


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'submitted_at', 'completed_at')



from workflows.examples.distributed_training_demo.estimate_resources import estimate_resources

class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = '__all__'

    def create(self, validated_data):

        # Verfier le type de workflow
        workflow_type = validated_data.get("workflow_type")
        if workflow_type not in [choice[0] for choice in Workflow.WorkflowType.choices]:
            raise serializers.ValidationError("Invalid workflow type.")
        
        if workflow_type == Workflow.WorkflowType.ML_TRAINING:
            # Vérifier les champs requis pour le type de workflow ML_TRAINING
            if not validated_data.get("executable_path"):
                raise serializers.ValidationError("executable_path is required for ML_TRAINING workflow type.")
            if not validated_data.get("inputs_path"):
                raise serializers.ValidationError("inputs_path is required for ML_TRAINING workflow type.")
            # Estimer les ressources pour le type de workflow ML_TRAINING
            executable_path = validated_data.get("executable_path")
            inputs_path = validated_data.get("inputs_path")

            if inputs_path:
                try:
                    resources = estimate_resources(inputs_path)
                    validated_data["estimated_resources"] = resources
                except Exception as e:
                    raise serializers.ValidationError(f"Resource estimation failed: {e}")

            return super().create(validated_data)



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        
        # Valider l'email
        email = attrs.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Un utilisateur avec cet email existe déjà."})
        
        return attrs
    
    def create(self, validated_data):
        try:
            # Créer l'utilisateur avec create_user pour gérer correctement le mot de passe
            user = User.objects.create_user(
                email=validated_data['email'],
                username=validated_data['username'],
                password=validated_data['password']
            )
            return user
        except Exception as e:
            import traceback
            print("Erreur lors de la création de l'utilisateur:", str(e))
            print(traceback.format_exc())
            raise

class WorkflowSerializer(serializers.ModelSerializer):
    owner_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'submitted_at', 'completed_at', 'owner', 'owner_username')
    
    def get_owner_username(self, obj):
        return obj.owner.username if obj.owner else None