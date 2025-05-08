# serializers.py
from rest_framework import serializers
from .models import Volunteer, VolunteerTask
from tasks.models import Task
from workflows.models import Workflow

class VolunteerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volunteer
        fields = '__all__'

class VolunteerTaskSerializer(serializers.ModelSerializer):
    volunteer = VolunteerSerializer(read_only=True)
    task = serializers.StringRelatedField()

    class Meta:
        model = VolunteerTask
        fields = '__all__'

class TaskWithVolunteerCountSerializer(serializers.ModelSerializer):
    volunteer_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'name', 'workflow', 'status', 'volunteer_count']

    def get_volunteer_count(self, obj):
        return obj.volunteer_tasks.count()

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

