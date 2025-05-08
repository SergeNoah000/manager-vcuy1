# backend/workflows/serializers.py
from rest_framework import serializers
from .models import Workflow

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
